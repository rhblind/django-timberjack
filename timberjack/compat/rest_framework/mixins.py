# -*- coding: utf-8 -*-

from django.contrib.admin.options import get_content_type_for_model
from django.utils.encoding import force_text

from timberjack.constants import CREATE, UPDATE, DELETE, READ
from timberjack.documents import ObjectAccessLog
from timberjack.utils import MethodActionMap, MessageGenerator


class AccessLogModelMixin(MessageGenerator):
    """
    Mixin class for `ModelViewSet` which writes object access log
    to mongodb.
    """

    default_log_level = 0
    method_action_map_class = MethodActionMap
    write_admin_log = False

    def log_object_action(self, request, obj, message):
        action_flag = self.get_method_action(request)

        if not action_flag:
            # Unsupported HTTP method; do nothing.
            return

        ObjectAccessLog.objects.log_action(user_pk=request.user.pk, content_type=get_content_type_for_model(obj),
                                           object_pk=obj.pk, object_repr=repr(obj), action_flag=action_flag,
                                           message=message, level=self.default_log_level,
                                           ip_address=request.META.get('HTTP_X_FORWARDED_FOR') or
                                                      request.META.get('REMOTE_ADDR'),
                                           write_admin_log=self.write_admin_log)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        self.log_object_action(self.request, instance,
                               message=[{'read': {
                                   'name': force_text(instance._meta.verbose_name),
                                   'object': force_text(instance)
                               }}])
        return super(AccessLogModelMixin, self).retrieve(request, *args, **kwargs)

    def perform_create(self, serializer):
        super(AccessLogModelMixin, self).perform_create(serializer)
        self.log_object_action(self.request, serializer.instance,
                               message=[{'created': {
                                   'name': force_text(serializer.instance._meta.verbose_name),
                                   'object': force_text(serializer.instance)
                               }}])

    def perform_update(self, serializer):
        super(AccessLogModelMixin, self).perform_update(serializer)
        self.log_object_action(self.request, serializer.instance,
                               message=[{'updated': {
                                   'name': force_text(serializer.instance._meta.verbose_name),
                                   'object': force_text(serializer.instance),
                                   'fields': list(serializer.validated_data.keys())
                               }}])

    def perform_destroy(self, instance):
        self.log_object_action(self.request, instance,
                               message=[{'deleted': {
                                   'name': force_text(instance._meta.verbose_name),
                                   'object': force_text(instance)
                               }}])
        super(AccessLogModelMixin, self).perform_destroy(instance)
