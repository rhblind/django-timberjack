# -*- coding: utf-8 -*-

import re

from django.contrib.contenttypes.models import ContentType

from mongoengine.fields import StringField


class ContentTypeField(StringField):
    """
    Store django ContentType references.
    """
    regex = re.compile(r'^(\w+)\.(\w+)')

    # TODO: Cache valid ContentType lookups.

    def __init__(self, *args, **kwargs):
        super(ContentTypeField, self).__init__(regex=self.regex, *args, **kwargs)

    def to_python(self, value):
        # TODO: Cache lookup
        app_label, model = value.split('.', 1)
        return ContentType.objects.get(app_label=app_label, model=model)

    def to_mongo(self, value):
        if isinstance(value, str):
            return '.'.join(self.regex.match(value).groups())
        if isinstance(value, ContentType):
            return '{app_label}.{model}'.format(app_label=value.app_label, model=value.model)

    def validate(self, value):
        if isinstance(value, str):
            try:
                # TODO: Cache lookup
                app_label, model = self.regex.match(value).groups()
                ContentType.objects.get(app_label=app_label, model=model)
            except (AttributeError, ContentType.DoesNotExist):
                self.error('Could not look up ContentType object for "%s".' % value)

        if isinstance(value, ContentType):
            value = '{app_label}.{model}'.format(app_label=value.app_label, model=value.model)

        super(ContentTypeField, self).validate(value)


