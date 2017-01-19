# -*- coding: utf-8 -*-

import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from mongoengine import *
from timberjack.fields import UserPKField, ModelField


def integer_validator(value):
    if not isinstance(value, int):
        raise DjangoValidationError('%(1)r is not an integer.',
                                    code='invalid',
                                    params={'value': value})


def uuid_validator(value):
    try:
        uuid.UUID(value)
    except ValueError:
        raise DjangoValidationError('%(value)s is not a valid UUID.',
                                    code='invalid',
                                    params={'value': value})


@override_settings(AUTH_USER_MODEL='timberjack.NoPKFieldUserModel')
class NoPKFieldUserTestCase(TestCase):
    """
    Test that a user model with no defined primary key works.
    """

    class NoPKFieldUserModel(AbstractBaseUser):
        username = models.CharField(max_length=255)
        USERNAME_FIELD = 'username'

        class Meta:
            app_label = 'timberjack'

    def setUp(self):
        self.field = UserPKField()

    def test_pk_field_is_autofield(self):
        self.assertIsInstance(self.field.pk_field, models.AutoField)

    def test_validate_integer(self):
        self.assertIsNone(self.field.validate(1))


@override_settings(AUTH_USER_MODEL='timberjack.IntegerUserModel')
class IntegerUserPKFieldTestCase(TestCase):
    """
    Test that a user model with a custom integer based primary key works.
    """

    class IntegerUserModel(AbstractBaseUser):
        id = models.IntegerField(primary_key=True, unique=True, validators=[integer_validator])
        username = models.CharField(max_length=255)
        USERNAME_FIELD = 'username'

        class Meta:
            app_label = 'timberjack'

    def setUp(self):
        self.field = UserPKField()

    def test_validate_integer(self):
        self.assertIsNone(self.field.validate(1))

    def test_validate_string_fails(self):
        try:
            self.field.validate('this is not an integer!')
            self.fail('Did not fail when trying to validate a string.')
        except ValidationError as e:
            self.assertEqual(str(e), "'this is not an integer!' value must be an integer.")

    def test_value_conversion(self):
        value = 1
        mongo_val = self.field.to_mongo(value)
        python_val = self.field.to_python(mongo_val)
        self.assertEqual(value, python_val)


@override_settings(AUTH_USER_MODEL='timberjack.StringUserModel')
class StringUserPKFieldTestCase(TestCase):
    """
    Test that a user model with a custom string based primary key works.
    """

    class StringUserModel(AbstractBaseUser):
        id = models.CharField(primary_key=True, unique=True, max_length=6)
        username = models.CharField(max_length=255)
        USERNAME_FIELD = 'username'

        class Meta:
            app_label = 'timberjack'

    def setUp(self):
        self.field = UserPKField()

    def test_validate_string(self):
        self.assertIsNone(self.field.validate('unique'))

    def test_validate_too_long_string_fails(self):
        try:
            self.field.validate('this string is more than 6 characters long!')
            self.fail('Did not fail when trying to validate a too long string.')
        except ValidationError as e:
            self.assertEqual(str(e), 'Ensure this value has at most 6 characters (it has 43).')

    def test_validate_int_fails(self):
        try:
            self.field.validate(1)
            self.fail('Did not fail when trying to validate a non string type.')
        except ValidationError as e:
            self.assertEqual(str(e), 'Value %(value)r is not a valid primary key value for '
                                     '<django.db.models.fields.CharField: id>.' % {'value': 1})

    def test_value_conversion(self):
        value = 'value'
        mongo_val = self.field.to_mongo(value)
        python_val = self.field.to_python(mongo_val)
        self.assertEqual(value, python_val)


@override_settings(AUTH_USER_MODEL='timberjack.UUIDUserModel')
class UUIDUserPKFieldTestCase(TestCase):
    """
    Test that a user model with a custom UUID based primary key works.
    """

    class UUIDUserModel(AbstractBaseUser):
        id = models.UUIDField(primary_key=True, unique=True, validators=[uuid_validator])
        username = models.CharField(max_length=255)
        USERNAME_FIELD = 'username'

        class Meta:
            app_label = 'timberjack'

    def setUp(self):
        self.field = UserPKField()

    def test_validate_uuid_string(self):
        self.assertIsNone(self.field.validate('6a3de76f-ebd6-448d-a70f-62e0866d37f4'))

    def test_validate_uuid_hex_string(self):
        self.assertIsNone(self.field.validate('74a40ec6a74d44199d8457861bb51484'))

    def test_validate_non_valid_uuid_fails(self):
        try:
            self.field.validate('this-is-not-an-uuid')
            self.fail('Did not fail when trying to validate a non-valid uuid string.')
        except ValidationError as e:
            self.assertEqual(str(e), "'this-is-not-an-uuid' is not a valid UUID.")

    def test_value_conversion(self):
        value = uuid.uuid4()
        mongo_val = self.field.to_mongo(value)
        python_val = self.field.to_python(mongo_val)
        self.assertEqual(value, python_val)


class ModelFieldTestCase(TestCase):
    """
    Make sure the ModelField can store and retrieve django model instances.
    """
    USER_MODEL = get_user_model()

    def setUp(self):
        self.field = ModelField()
        self.user = self.USER_MODEL.objects.create_user(username='testuser', email='testuser@example.com',
                                                        password='test123.')

    def test_user_instance_validate(self):
        self.assertIsNone(self.field.validate(self.user))

    def test_invalid_value(self):
        try:
            self.field.validate(['this', 'is', 'a', 'list'])
            self.fail('Did not fail when trying to validate a non-valid value.')
        except ValidationError as e:
            self.assertEqual(str(e), "Value ['this', 'is', 'a', 'list'] is not a django.db.models.Model instance.")

    def test_value_conversion(self):
        value = self.user
        mongo_val = self.field.to_mongo(value)
        python_val = self.field.to_python(mongo_val)
        self.assertEqual(value, python_val)

    def test_model_field_instance(self):

        class UserDocument(Document):
            user = ModelField()

        UserDocument.drop_collection()

        instance = UserDocument(user=self.user)
        instance.save()

        self.assertIsInstance(instance.user, self.USER_MODEL)

    def test_model_field_filter(self):

        class UserDocument(Document):
            user = ModelField()
            timestamp = DateTimeField(required=True, default=timezone.now)

        UserDocument.drop_collection()

        for i in range(1, 10):
            defaults = {
                'username': 'user%d' % i,
                'email': 'user%d@example.com' % i,
                'password': 'test123.'
            }
            user = self.USER_MODEL.objects.create_user(**defaults)
            UserDocument.objects.create(user=user)

        self.assertEqual(UserDocument.objects.get(user__fields__username='user1').user,
                         self.USER_MODEL.objects.get(username='user1'))

        self.assertEqual(UserDocument.objects.get(user__pk=2).user,
                         self.USER_MODEL.objects.get(pk=2))
