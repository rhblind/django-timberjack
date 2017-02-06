# -*- coding: utf-8 -*-

import json
import logging

from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.encoding import smart_text, force_text
from django.utils.text import get_text_list
from django.utils.translation import ugettext, ugettext_lazy as _

from mongoengine import *
from mongoengine.queryset import QuerySet

from timberjack.fields import ModelField
from timberjack.validators import validate_ip_address

LOG_LEVEL = (
    (0, _('NOTSET')),
    (10, _('DEBUG')),
    (20, _('INFO')),
    (30, _('WARNING')),
    (40, _('ERROR')),
    (50, _('CRITICAL'))
)

logger = logging.getLogger(__name__)
USER_MODEL = get_user_model()


class ObjectAccessLogQuerySet(QuerySet):

    def log_action(self, user, content_type, object_pk, object_repr,
                   action_flag, message='', log_level=20, ip_address=None, write_admin_log=False):
        if isinstance(message, list):
            message = json.dumps(message)
        return self._document(
            user=user,
            content_type=content_type,
            object_pk=object_pk,
            object_repr=object_repr[:200],
            action_flag=action_flag,
            message=message,
            log_level=log_level,
            ip_address=ip_address
        ).save(write_admin_log=write_admin_log)


class ObjectAccessLog(Document):
    """
    Store log entries.
    """
    CREATE_ACTION = ADDITION
    UPDATE_ACTION = CHANGE
    DELETE_ACTION = DELETION
    READ_ACTION = 4
    ACTIONS = (
        (CREATE_ACTION, _('Created')),
        (UPDATE_ACTION, _('Updated')),
        (DELETE_ACTION, _('Deleted')),
        (READ_ACTION, _('Read'))
    )

    meta = {
        'queryset_class': ObjectAccessLogQuerySet,
        'indexes': [
            '*user.pk',
            '*user.fields.username',
            '*content_type.pk',
        ]
    }

    message = StringField(default='')
    action_flag = IntField(min_value=1, max_value=4, choices=ACTIONS, required=True)
    log_level = IntField(choices=LOG_LEVEL, default=20)
    object_pk = DynamicField(required=True)
    content_type = ModelField(required=True)
    object_repr = StringField(max_length=200, required=True)
    user = ModelField(required=True)
    ip_address = StringField(validation=validate_ip_address)
    admin_log_pk = IntField(default=None)
    referrer = ReferenceField('self', default=None)
    timestamp = DateTimeField(required=True, default=timezone.now)

    def __repr__(self):
        return smart_text(self.timestamp)

    def __str__(self):
        if self.is_create_action:
            return ugettext('Added "%(object)s".') % {'object': self.object_repr}
        elif self.is_update_action:
            return ugettext('Changed "%(object)s - %(changes)s".') % {
                'object': self.object_repr,
                'changes': self.get_log_message()
            }
        elif self.is_delete_action:
            return ugettext('Deleted "%(object)s".') % {'object': self.object_repr}
        elif self.is_read_action:
            return ugettext('Read "%(object)s".') % {'object': self.object_repr}

        return ugettext('ObjectAccessLog Object')

    @property
    def is_create_action(self):
        return self.action_flag == ObjectAccessLog.CREATE_ACTION

    @property
    def is_read_action(self):
        return self.action_flag == ObjectAccessLog.READ_ACTION

    @property
    def is_update_action(self):
        return self.action_flag == ObjectAccessLog.UPDATE_ACTION

    @property
    def is_delete_action(self):
        return self.action_flag == ObjectAccessLog.DELETE_ACTION

    @property
    def is_json_message(self):
        return self.message and self.message[0] == '['

    def get_human_message(self, include_fullname=False, include_context=False):
        """
        Get a human readable log message.
        :param include_fullname: Default to False. Set to True to include users full name
                                 in log message. Might cause UnicodeDecodeErrors for some 3rd
                                 party libraries, or leaking sensitive information.
        :param include_context: Whether to include a machine readable context. If included,
                                the context will be separated from the string message by a
                                new line character(\n).
        """
        if self.is_json_message:
            _log_message = self.get_log_message()
            parsed_message = _log_message[0].lower() + _log_message[1:]
        else:
            parsed_message = str(self)[0].lower() + str(self)[1:]

        message = 'User "{username}" {str_action} at {timestamp}{ip_addr}.'.format(
            username=''.join((self.user.get_username(), ' ({fullname})'.format(fullname=self.user.get_full_name())
                              if include_fullname and self.user.get_full_name() else '')),
            str_action=parsed_message.rstrip('.'),
            timestamp='{:%B %d, %Y %H:%M:%S}'.format(self.timestamp),
            ip_addr=' from IP-address %s' % self.ip_address if self.ip_address else '')
        if include_context:
            message = '{message}\n{context}'.format(
                message=message,
                context=json.dumps({
                    'pk': str(self.pk),
                    'action_flag': self.action_flag,
                    'content_type': '{app_label}.{model}'.format(app_label=self.content_type.app_label,
                                                                 model=self.content_type.model),
                    'user_pk': self.user.pk,
                    'object_pk': self.object_pk,
                    'timestamp': str(self.timestamp),
                    'ip_address': self.ip_address,
                    'referrer': str(self.referrer.pk) if self.referrer else None,
                }))
        return message

    def get_log_message(self):
        """
        (Copied from `django.contrib.admin.models.LogEntry.get_change_message()`)
        If self.message is a JSON structure, interpret it as a change string, properly translated.
        """
        if self.is_json_message:
            try:
                message = json.loads(self.message)
            except ValueError:
                return self.message
            messages = []
            for sub_message in message:
                if 'added' in sub_message:
                    if sub_message['added']:
                        sub_message['added']['name'] = ugettext(sub_message['added']['name'])
                        messages.append(ugettext('Added {name} "{object}".').format(**sub_message['added']))
                    else:
                        messages.append(ugettext('Added.'))

                elif 'changed' in sub_message:
                    sub_message['changed']['fields'] = get_text_list(
                        sub_message['changed']['fields'], ugettext('and')
                    )
                    if 'name' in sub_message['changed']:
                        sub_message['changed']['name'] = ugettext(sub_message['changed']['name'])
                        messages.append(ugettext('Changed {fields} for {name} "{object}".').format(
                            **sub_message['changed']
                        ))
                    else:
                        messages.append(ugettext('Changed {fields}.').format(**sub_message['changed']))

                elif 'deleted' in sub_message:
                    sub_message['deleted']['name'] = ugettext(sub_message['deleted']['name'])
                    messages.append(ugettext('Deleted {name} "{object}".').format(**sub_message['deleted']))

                elif 'read' in sub_message:
                    if sub_message['read']:
                        sub_message['read']['name'] = ugettext(sub_message['read']['name'])
                        messages.append(ugettext('Read {name} "{object}".').format(**sub_message['read']))
                    else:
                        messages.append(ugettext('Read.'))

            message = ' '.join(msg[0].upper() + msg[1:] for msg in messages)
            return message or ugettext('No fields changed.')
        else:
            return self.message

    def get_admin_log_object(self):
        """
        If saved with an `admin_log_pk` attribute, look up
        and return the corresponding object.
        """
        if not self.admin_log_pk:
            return None
        try:
            return LogEntry.objects.get(pk=self.admin_log_pk)
        except LogEntry.DoesNotExist:
            return None

    def get_content_object(self):
        return self.content_type.get_object_for_this_type(pk=self.object_pk)

    def save(self, *args, **kwargs):
        logger.log(self.log_level, msg=self.get_human_message(include_context=True))
        if kwargs.get('write_admin_log', False) is True:
            if self.is_read_action:
                logger.debug('Read actions are not written to the `admin.LogEntry` table due '
                             'to missing support for read actions.')
            else:
                self.admin_log_pk = LogEntry.objects.create(user_id=self.user.pk, content_type_id=self.content_type.pk,
                                                            object_id=self.object_pk,
                                                            object_repr=force_text(
                                                                self.content_type.get_object_for_this_type(
                                                                    pk=self.object_pk))[:200],
                                                            action_flag=self.action_flag,
                                                            change_message=self.message).pk
        return super(ObjectAccessLog, self).save(*args, **kwargs)
