# -*- coding: utf-8 -*-

import json

from django.contrib.admin.models import LogEntry

from django.utils import timezone
from django.utils.encoding import smart_text
from django.utils.translation import ugettext, ugettext_lazy as _

from mongoengine import *
from mongoengine.queryset import QuerySet

from timberjack.fields import ContentTypeField, UserPKField
from timberjack.validators import validate_ip_address

# We want to log CRUD actions.
# (keep numerical values compatible with admin.LogEntry model)
CREATE = 1
UPDATE = 2
DELETE = 3
READ = 4

LOG_LEVEL = (
    (0, _('NOTSET')),
    (10, _('DEBUG')),
    (20, _('INFO')),
    (30, _('WARNING')),
    (40, _('ERROR')),
    (50, _('CRITICAL'))
)


class ObjectAccessLogQuerySet(QuerySet):

    def log_action(self, user_pk, content_type, object_pk, object_repr,
                   action_flag, message, level=0, ip_address=None, write_admin_log=False):
        if isinstance(message, list):
            message = json.dumps(message)
        return self._document(
            user_pk=user_pk,
            content_type=content_type,
            object_pk=object_pk,
            object_repr=object_repr[:200],
            action_flag=action_flag,
            message=message,
            level=level,
            ip_address=ip_address
        ).save(write_admin_log=write_admin_log)


class ObjectAccessLog(Document):

    meta = {
        'queryset_class': ObjectAccessLogQuerySet
    }

    message = StringField(default='')
    action_flag = IntField(min_value=1, max_value=4, required=True)
    level = IntField(choices=LOG_LEVEL, default=0)
    object_pk = DynamicField(required=True)
    content_type = ContentTypeField(required=True)
    object_repr = StringField(max_length=200, required=True)
    user_pk = UserPKField(required=False)
    ip_address = StringField(validation=validate_ip_address, required=False)
    admin_log_pk = IntField(required=False, default=None)
    timestamp = DateTimeField(required=True, default=timezone.now)

    def __repr__(self):
        return smart_text(self.timestamp)

    def __str__(self):
        if self.is_create_action:
            return ugettext('Created "%(object)s.') % {'object': self.object_repr}
        elif self.is_update_action:
            return ugettext('Updated "%(object)s - %(changes)s"') % {
                'object': self.object_repr,
                'changes': self.get_change_message()
            }
        elif self.is_delete_action:
            return ugettext('Deleted "%(object)s."') % {'object': self.object_repr}
        elif self.is_read_action:
            return ugettext('Read "%(object)s."') % {'object': self.object_repr}

        return ugettext('ObjectAccessLog Object')

    @property
    def is_create_action(self):
        return self.action_flag == CREATE

    @property
    def is_read_action(self):
        return self.action_flag == READ

    @property
    def is_update_action(self):
        return self.action_flag == UPDATE

    @property
    def is_delete_action(self):
        return self.action_flag == DELETE

    def get_change_message(self):
        """
        See admin.LogEntry.
        """
        # TODO: Do a proper implementation
        return self.message or 'No record!'

    def get_admin_log_object(self):
        """
        If saved with an `admin_log_pk` attribute, look up
        and return the corresponding object.
        """
        if not self.admin_log_pk:
            return None
        return LogEntry.objects.get(pk=self.admin_log_pk)

    def save(self, *args, **kwargs):
        if kwargs.get("write_admin_log", False) is True:
            if self.is_read_action:
                # TODO: Unsupported action - should inform user!
                pass
            else:
                self.admin_log_pk = LogEntry.objects.create(user_id=self.user_pk, content_type_id=self.content_type.pk,
                                                            object_id=self.object_pk,
                                                            object_repr=repr(self.content_type.get_object_for_this_type(
                                                                pk=self.object_pk))[:200], action_flag=self.action_flag,
                                                            change_message=self.get_change_message()).pk
        return super(ObjectAccessLog, self).save(*args, **kwargs)

