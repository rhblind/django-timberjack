# -*- coding: utf-8 -*-

import json
from django.db.models import Model
from django.core import serializers

from mongoengine.dereference import DeReference
from mongoengine.base.datastructures import BaseDict


class DjangoModelDereference(DeReference):
    """
    Dereferences a Django model.
    """
    def __call__(self, items, max_depth=1, instance=None, name=None):
        self.max_depth = max_depth
        if isinstance(items, Model):
            serialized = serializers.serialize('json', [items])
            serialized = json.loads(serialized[1:-1])

            defaults = serialized.pop("fields")
            defaults.update({"pk": serialized.pop("pk")})

            self.reference_map = self._find_references(defaults)
            self.object_map = self._fetch_objects(doc_type=None)
            return self._attach_objects(defaults, 0, instance, name)
        return super(DjangoModelDereference, self).__call__(items, max_depth, instance, name)


class MapBaseDict(BaseDict):
    """
    BaseDict which supports looking up attributes using dot notation.
    """
    def __init__(self, dict_items, instance, name):
        super(MapBaseDict, self).__init__(dict_items, instance, name)

        for key, value in dict_items.items():
            self[key] = value

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value, *args, **kwargs):
        super(MapBaseDict, self).__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, key, *args, **kwargs):
        self.__delitem__(key)

    def __delitem__(self, key, *args, **kwargs):
        super(MapBaseDict, self).__delitem__(key)
        del self.__dict__[key]


class DjangoModelDereferenceMixin(object):
    """
    Mixin class which overrides __get__ behaviour for ModelFields
    """
    def __get__(self, instance, owner):
        if instance is None:
            return self

        dereference = DjangoModelDereference()
        if instance._initialised and instance._data.get(self.name):
            instance._data[self.name] = dereference(
                instance._data.get(self.name), max_depth=1, instance=instance,
                name=self.name
            )
        value = super(DjangoModelDereferenceMixin, self).__get__(instance, owner)
        return MapBaseDict(dict_items={key: value for key, value in value.items()},
                           instance=instance, name=value._name)
