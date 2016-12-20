# -*- coding: utf-8 -*-

import re
import operator
from functools import reduce

from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from mongoengine import fields

_ctype_cache = {}


class ContentTypeField(fields.StringField):
    """
    Store django ContentType references.
    """
    regex = re.compile(r'^(\w+)\.(\w+)')

    def __init__(self, *args, **kwargs):
        super(ContentTypeField, self).__init__(regex=self.regex, *args, **kwargs)

    def to_python(self, value):
        if isinstance(value, ContentType):
            ctype_string = '{app_label}.{model}'.format(app_label=value.app_label, model=value.model)
            if ctype_string not in _ctype_cache:
                _ctype_cache[ctype_string] = value
            return value

        elif isinstance(value, str):
            try:
                return _ctype_cache[value]
            except KeyError:
                app_label, model = value.split('.', 1)
                ctype_string = '{app_label}.{model}'.format(app_label=app_label, model=model)
                if ctype_string not in _ctype_cache:
                    _ctype_cache[ctype_string] = ContentType.objects.get(app_label=app_label, model=model)
            finally:
                return _ctype_cache[value]

    def to_mongo(self, value):
        if isinstance(value, str):
            return '.'.join(self.regex.match(value).groups())
        if isinstance(value, ContentType):
            return '{app_label}.{model}'.format(app_label=value.app_label, model=value.model)

    def validate(self, value):
        if isinstance(value, str):
            try:
                app_label, model = self.regex.match(value).groups()
                value = '{app_label}.{model}'.format(app_label=app_label, model=model)
                if value not in _ctype_cache:
                    _ctype_cache.update({value: ContentType.objects.get(app_label=app_label, model=model)})
            except (AttributeError, ContentType.DoesNotExist):
                self.error('Could not look up ContentType object for "%s".' % value)

        if isinstance(value, ContentType):
            value = '{app_label}.{model}'.format(app_label=value.app_label, model=value.model)

        super(ContentTypeField, self).validate(value)


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

