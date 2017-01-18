# -*- coding: utf-8 -*-

from django.contrib import admin
from django.contrib.admin.options import get_content_type_for_model
from django.utils.encoding import force_text

from timberjack.documents import ObjectAccessLog


class TimberjackMixin(admin.ModelAdmin):

    default_log_level = 20

    def _get_request_address(self, request):
        return request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR')

    def _update_message(self, action, object, message):
        """
        Make sure the message has object context.
        """
        for entry in message:
            if isinstance(entry, dict) and not all(k for k in ('name', 'object')) in entry.values():
                if action in entry:
                    entry[action].update({'name': force_text(object._meta.verbose_name),
                                          'object': force_text(object)})
        return message

    def get_object(self, request, object_id, from_field=None):
        instance = super(TimberjackMixin, self).get_object(request, object_id, from_field)
        if instance:
            self.log_read(request, instance, force_text(instance))
        return instance

    def log_addition(self, request, object, message):
        """
        Log that an object has been successfully added.
        Overrides default behaviour, but will write an `admin.LogEntry` entry
        for the action as well.
        """
        if isinstance(message, list):
            message = self._update_message('added', object, message)
        ObjectAccessLog.objects.log_action(user=request.user, content_type=get_content_type_for_model(object),
                                           object_pk=object.pk, object_repr=force_text(object),
                                           log_level=self.default_log_level,
                                           ip_address=self._get_request_address(request),
                                           action_flag=ObjectAccessLog.CREATE_ACTION,
                                           message=message, write_admin_log=True)

    def log_change(self, request, object, message):
        """
        Log that an object has been successfully changed.
        Overrides default behaviour, but will write an `admin.LogEntry` entry
        for the action as well.
        """
        if isinstance(message, list):
            message = self._update_message('changed', object, message)
        ObjectAccessLog.objects.log_action(user=request.user, content_type=get_content_type_for_model(object),
                                           object_pk=object.pk, object_repr=force_text(object),
                                           log_level=self.default_log_level,
                                           ip_address=self._get_request_address(request),
                                           action_flag=ObjectAccessLog.UPDATE_ACTION,
                                           message=message, write_admin_log=True)

    def log_deletion(self, request, object, object_repr):
        """
        Log that an object will be deleted.
        Overrides default behaviour, but will write an `admin.LogEntry` entry
        for the action as well.
        """
        message = self._update_message('deleted', object, message=[{'deleted': {}}])
        ObjectAccessLog.objects.log_action(user=request.user, content_type=get_content_type_for_model(object),
                                           object_pk=object.pk, object_repr=object_repr,
                                           log_level=self.default_log_level,
                                           ip_address=self._get_request_address(request),
                                           action_flag=ObjectAccessLog.DELETE_ACTION,
                                           message=message, write_admin_log=True)

    def log_read(self, request, object, object_repr):
        """
        Log that an object has been successfully read. The default behaviour will
        write a log entry to the  `timberjack.ObjectAccessLog` table in MongoDB.
        No entry will be written to `admin.LogEntry` since it does not support read
        actions.
        """
        message = self._update_message('read', object, message=[{'read': {}}])
        ObjectAccessLog.objects.log_action(user=request.user, content_type=get_content_type_for_model(object),
                                           object_pk=object.pk, object_repr=object_repr,
                                           log_level=self.default_log_level,
                                           ip_address=self._get_request_address(request),
                                           action_flag=ObjectAccessLog.READ_ACTION,
                                           message=message, write_admin_log=False)
