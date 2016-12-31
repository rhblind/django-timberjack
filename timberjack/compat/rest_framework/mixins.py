# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType

from timberjack.documents import CREATE, UPDATE, DELETE, READ, ObjectAccessLog


class MethodActionMap(object):
    action_map = {
        "GET": READ,
        "POST": CREATE,
        "PUT": UPDATE,
        "PATCH": UPDATE,
        "DELETE": DELETE,
    }

    def __init__(self, request):
        self._method = request.method

    @property
    def method(self):
        return self.action_map.get(self._method, None)


class ObjectAccessLogMixin(object):
    """
    Provides logging for actions performed on Rest Framework Views.
    """

    method_action_map_class = MethodActionMap
    default_log_level = 0
    write_admin_log = False

    def get_method_action_map_class(self):
        assert self.method_action_map_class is not None, (
            "'%s' should either include a `method_action_map_class` attribute, "
            "or override the `get_method_action_map_class()` method."
            % self.__class__.__name__
        )
        return self.method_action_map_class

    def get_method_action(self, request):
        method_action_class = self.get_method_action_map_class()
        return method_action_class(request).method

    def log_object_action(self, request, obj):
        action_flag = self.get_method_action(request)

        if not action_flag:
            # Unsupported HTTP method; do nothing.
            return

        # TODO: Construct message
        message = 'To be constructed'
        ObjectAccessLog.objects.log_action(user_pk=request.user.pk, content_type=ContentType.objects.get_for_model(obj),
                                           object_pk=obj.pk, object_repr=repr(obj), action_flag=action_flag,
                                           message=message, level=self.default_log_level,
                                           ip_address=request.META.get('HTTP_X_FORWARDED_FOR') or
                                                      request.META.get('REMOTE_ADDR'),
                                           write_admin_log=self.write_admin_log)

    def get_object(self):
        obj = super(ObjectAccessLogMixin, self).get_object()
        self.log_object_action(self.request, obj)
        return obj
