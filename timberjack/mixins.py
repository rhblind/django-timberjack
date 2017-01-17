# -*- coding: utf-8 -*-

from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.forms import modelform_factory, ALL_FIELDS
from timberjack.documents import ObjectAccessLog


class MethodActionMap(object):
    """
    Class which maps HTTP methods to user actions.
    """
    action_map = {
        "GET": ObjectAccessLog.READ_ACTION,
        "POST": ObjectAccessLog.CREATE_ACTION,
        "PUT": ObjectAccessLog.UPDATE_ACTION,
        "PATCH": ObjectAccessLog.UPDATE_ACTION,
        "DELETE": ObjectAccessLog.DELETE_ACTION,
    }

    def __init__(self, request):
        self._method = request.method

    @property
    def method(self):
        return self.action_map.get(self._method, None)


class BaseObjectAccessLogMixin(object):
    """
    Some docstring here..
    """
    method_action_map_class = MethodActionMap

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

    def get_form(self, request, obj):
        return modelform_factory(apps.get_model(obj._meta.app_label, obj._meta.model_name),
                                 fields=ALL_FIELDS)

    def construct_message(self, request, obj=None):
        """
        Constructs a log message for the requested object. Optionally,
        pass a custom form used to figure out changed data.
        """
        action_flag = self.get_method_action(request)

        ModelForm = self.get_form(request, obj)
        if request.method == 'POST':
            form = ModelForm(request.POST, request.FILES, instance=obj)
        else:
            # NOTE: Do we need to care about this one?
            if action_flag is ObjectAccessLog.CREATE_ACTION:
                initial = dict(request.GET.items())
                for key in initial:
                    try:
                        field = obj._meta.model._meta.get_field(key)
                    except FieldDoesNotExist:
                        continue
                    if isinstance(field, models.ManyToManyField):
                        initial[key] = initial[key].split(',')
                form = ModelForm(initial=initial)
            else:
                form = ModelForm(instance=obj)

        message = []
        if action_flag is ObjectAccessLog.CREATE_ACTION:
            message.append({'created': {}})
        elif action_flag is ObjectAccessLog.READ_ACTION:
            message.append({'read': {}})
        elif action_flag is ObjectAccessLog.UPDATE_ACTION:
            message.append({'updated': {'fields': form.changed_data}})
        elif action_flag is ObjectAccessLog.DELETE_ACTION:
            message.append({'deleted': {}})

        return message
