# -*- coding: utf-8 -*-

from django.contrib.admin.options import get_content_type_for_model
from django.utils.encoding import force_text

from timberjack.documents import ObjectAccessLog
from timberjack.mixins import MethodActionMap, BaseObjectAccessLogMixin


class AccessLogModelViewMixin(BaseObjectAccessLogMixin):
    """
    Mixin class for `ModelViewSet` which writes object access log
    to mongodb.
    """
    default_log_level = 20
    method_action_map_class = MethodActionMap
    write_admin_log = False

    def log_object_action(self, request, obj, message):
        action_flag = self.get_method_action(request)

        if not action_flag:
            # Unsupported HTTP method; do nothing.
            return

        ObjectAccessLog.objects.log_action(user=request.user, content_type=get_content_type_for_model(obj),
                                           object_pk=obj.pk, object_repr=repr(obj), action_flag=action_flag,
                                           message=message, log_level=self.default_log_level,
                                           ip_address=request.META.get('HTTP_X_FORWARDED_FOR') or
                                                      request.META.get('REMOTE_ADDR'),
                                           write_admin_log=self.write_admin_log)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if self.request.user.is_authenticated():
            self.log_object_action(self.request, instance,
                                   message=[{'read': {
                                       'name': force_text(instance._meta.verbose_name),
                                       'object': force_text(instance)
                                   }}])
        return super(AccessLogModelViewMixin, self).retrieve(request, *args, **kwargs)

    def perform_create(self, serializer):
        super(AccessLogModelViewMixin, self).perform_create(serializer)
        if self.request.user.is_authenticated():
            self.log_object_action(self.request, serializer.instance,
                                   message=[{'added': {
                                       'name': force_text(serializer.instance._meta.verbose_name),
                                       'object': force_text(serializer.instance)
                                   }}])

    def perform_update(self, serializer):
        super(AccessLogModelViewMixin, self).perform_update(serializer)
        if self.request.user.is_authenticated():
            self.log_object_action(self.request, serializer.instance,
                                   message=[{'changed': {
                                       'name': force_text(serializer.instance._meta.verbose_name),
                                       'object': force_text(serializer.instance),
                                       'fields': list(serializer.validated_data.keys())
                                   }}])

    def perform_destroy(self, instance):
        if self.request.user.is_authenticated():
            self.log_object_action(self.request, instance,
                                   message=[{'deleted': {
                                       'name': force_text(instance._meta.verbose_name),
                                       'object': force_text(instance)
                                   }}])
        super(AccessLogModelViewMixin, self).perform_destroy(instance)
