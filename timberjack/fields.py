# -*- coding: utf-8 -*-

import re
import json
import operator
from functools import reduce

from django.core import serializers
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.base import DeserializationError
from django.db.models import Model
from django.utils import six
from django.utils.translation import ugettext_lazy as _
from mongoengine import fields

from timberjack.dereference import DjangoModelDereferenceMixin


class UserPKField(fields.DynamicField):
    """
    Dynamic field which piggybacks on the settings.AUTH_USER_MODEL
    validation and value converting.
    """
    default_error_messages = {
        'non_field_error': _('Value %(value)r is not a valid primary key value for %(field)r.')
    }

    @property
    def pk_field(self):
        model = get_user_model()
        pk_field = reduce(operator.eq,
                          filter(lambda field: field.primary_key, model._meta.fields))
        return pk_field

    def to_python(self, value):
        return self.pk_field.to_python(value)

    def to_mongo(self, value, **kwargs):
        # NOTE: This is probably way to naive!
        return self.to_python(value)

    def validate(self, value, clean=True):
        try:
            self.pk_field.run_validators(value)
        except ValidationError as e:
            if hasattr(e, 'code') and e.code in self.pk_field.error_messages:
                e.message = self.pk_field.error_messages[e.code]
            message = getattr(e, 'message', '. '.join(e.messages))
            self.error(message)
        except Exception:
            # All other exceptions are recorded as 'non_field_error'.
            message = self.default_error_messages['non_field_error'] % {
                'value': value,
                'field': self.pk_field
            }
            self.error(message)


class ModelField(DjangoModelDereferenceMixin, fields.DictField):
    """
    Store a serialized model instance.
    """
    default_error_messages = {
        'required': _('Field is required and cannot be empty'),
        'non_model_instance': _('Value %(value)r is not a django.db.models.Model instance.')
    }

    def to_python(self, value):
        value = super(ModelField, self).to_python(value)
        if isinstance(value, dict) and all(key in value for key in ('fields', 'model', 'pk')):
            try:
                deserialized = next(serializers.deserialize('json', '[{value}]'.format(value=json.dumps(value)),
                                                            ignorenonexistent=True), None)
                value = getattr(deserialized, 'object', None)
            except DeserializationError:
                pass
        return value

    def to_mongo(self, value, use_db_field=True, fields=None, **options):
        if isinstance(value, Model):
            value = serializers.serialize('json', [value], **options)
            value = json.loads(value[1:-1])  # Trim off square brackets!
        return super(ModelField, self).to_mongo(value, use_db_field, fields)

    def validate(self, value):
        if isinstance(value, dict):
            return super(ModelField, self).validate(value)

        if self.required and not value:
            self.error(self.default_error_messages['required'])

        if not isinstance(value, Model):
            message = self.default_error_messages['non_model_instance'] % {
                'value': value
            }
            self.error(message)


