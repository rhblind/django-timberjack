# -*- coding: utf-8 -*-

import json
from django.db.models import Model
from django.core import serializers

from mongoengine.dereference import DeReference


class DjangoModelDereference(DeReference):
    """
    Dereferences a Django model.
    """
    def __call__(self, items, max_depth=1, instance=None, name=None):
        self.max_depth = max_depth
        if isinstance(items, Model):
            serialized = serializers.serialize('json', [items])
            serialized = json.loads(serialized[1:-1])

            self.reference_map = self._find_references(serialized['fields'])
            self.object_map = self._fetch_objects(doc_type=None)
            return self._attach_objects(serialized, 0, instance, name)
        return super(DjangoModelDereference, self).__call__(items, max_depth, instance, name)


class DjangoModelDereferenceMixin(object):
    """
    Mixin class which overrides __get__ behaviour for ModelFields
    so it returns Model instances if possible.
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
        return self.to_python(value)
