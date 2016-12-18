# -*- coding: utf-8 -*-

from django.test import TestCase
from mongoengine import ValidationError
from timberjack.validators import validate_ip_address


class ValidateIPAddressTestCase(TestCase):

    def test_validate_valid_ip_address(self):
        values = ['1.1.1.1', '255.0.0.0', '0.0.0.0', 'fe80::1', '::1', '1:2:3:4:5:6:7:8']
        for value in values:
            self.assertIsNone(validate_ip_address(value))

    def test_validate_invalid_ip_address(self):
        values = ['256.1.1.1', '25.1.1.', '25,1,1,1', '25.1 .1.1', '1:2', '::zzz', '12345::']
        for value in values:
            self.assertRaises(ValidationError, validate_ip_address, value)
