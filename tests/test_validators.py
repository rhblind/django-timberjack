# -*- coding: utf-8 -*-

from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from timberjack.validators import validate_ip_address, validate_content_type


class ValidateIPAddressTestCase(TestCase):
    pass


class ValidateContentTypeTestCase(TestCase):

    def test_content_type_string(self):
        value = 'auth.user'
        self.assertIsNone(validate_content_type(value))


