# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.test import TestCase, override_settings

from mongoengine import ValidationError
from timberjack.fields import ContentType, ContentTypeField, UserPKField


class ContentTypeFieldTestCase(TestCase):

    def setUp(self):
        self.field = ContentTypeField()

    def test_regex(self):
        self.assertIsNone(self.field.regex.match('auth'))
        self.assertIsNone(self.field.regex.match('auth user'))

        app_label, model = self.field.regex.match('auth.user').groups()
        self.assertEqual(app_label, 'auth')
        self.assertEqual(model, 'user')

        app_label, model = self.field.regex.match('auth.user.should.not.match').groups()
        self.assertEqual(app_label, 'auth')
        self.assertEqual(model, 'user')

        try:
            self.field.regex.match('auth').groups()
            self.fail('Did not fail when trying to call method on non-matched result')
        except AttributeError as e:
            self.assertEqual(str(e), "'NoneType' object has no attribute 'groups'")

    def test_validate_ctype_string(self):
        self.assertIsNone(self.field.validate('auth.user'))

    def test_validate_ctype_instance(self):
        ctype = ContentType.objects.get(app_label='auth', model='user')
        self.assertIsNone(self.field.validate(ctype))
        
    def test_validate_invalid_ctype_string(self):
        try:
            self.field.validate('invalid')
            self.fail('Did not fail when validating invalid content type string.')
        except ValidationError as e:
            self.assertEqual(str(e), 'Could not look up ContentType object for "invalid".')

    def test_validate_non_existent_ctype(self):
        try:
            self.field.validate('invalid.model')
            self.fail('Did not fail when trying to look up non-existent ContentType.')
        except ValidationError as e:
            self.assertEqual(str(e), 'Could not look up ContentType object for "invalid.model".')

    def test_ctype_string_to_python(self):
        self.assertEqual(
            self.field.to_python('auth.user'),
            ContentType.objects.get(app_label='auth', model='user'),
        )

    def test_ctype_string_to_mongo(self):
        self.assertEqual(self.field.to_mongo('auth.user'), 'auth.user')

    def test_ctype_instance_to_mongo(self):
        self.assertEqual(
            self.field.to_mongo(ContentType.objects.get(app_label='auth', model='user')),
            'auth.user'
        )


@override_settings(AUTH_USER_MODEL='timberjack.IntegerUserModel')
class UserPKFieldTestCase(TestCase):

    class IntegerUserModel(AbstractBaseUser):
        username = models.CharField(max_length=255)
        USERNAME_FIELD = 'username'

        class Meta:
            app_label = 'timberjack'

    def setUp(self):
        self.field = UserPKField()

    def test_validate_integer(self):
        self.assertIsNone(self.field.validate(1))

    # def test_validate_string_fails(self):
    #     try:
    #         self.field.validate('this is not an integer!')
    #         self.fail('Did not fail when trying to validate a string.')
    #     except Exception as e:
    #         self.fail(str(e))


@override_settings(AUTH_USER_MODEL='timberjack.StringUserModel')
class StringUserPKFieldTestCase(TestCase):

    class StringUserModel(AbstractBaseUser):
        id = models.CharField(primary_key=True, unique=True, max_length=255)
        username = models.CharField(max_length=255)
        USERNAME_FIELD = 'username'

        class Meta:
            app_label = 'timberjack'

    def setUp(self):
        self.field = UserPKField()

    def test_validate_string(self):
        self.assertIsNone(self.field.validate('unique string'))

    def test_validate_non_int_fails(self):
        try:
            self.assertRaises(ValidationError, self.field.validate, 1)
            self.fail('Did not fail when trying to validate a non string type.')
        except TypeError as e:
            self.assertEqual(str(e), "object of type 'int' has no len()")

