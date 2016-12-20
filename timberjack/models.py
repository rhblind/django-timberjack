# -*- coding: utf-8 -*-

from django.utils import timezone
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

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

    def log_action(self, user_id, content_type_id, object_id,
                   object_repr, action_flag, message='', write_admin_log=False):
        raise NotImplementedError


class ObjectAccessLog(Document):

    meta = {
        'db_alias': 'timberjack',
        'queryset_class': ObjectAccessLogQuerySet
    }

    message = StringField(default='')
    action_flag = IntField(min_value=1, max_value=4, required=True)
    level = IntField(choices=LOG_LEVEL, default=0)
    object_pk = StringField(required=True)
    content_type = ContentTypeField(required=True)
    user_pk = UserPKField(required=False)
    ip_address = StringField(validation=validate_ip_address, required=False)
    timestamp = DateTimeField(required=True, default=timezone.now)

    def __repr__(self):
        return force_text(self.timestamp)

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
        raise NotImplementedError

    def write_admin_log(self):
        """
        Write a copy to the django admin log.
        """
        raise NotImplementedError
