# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from mongoengine import *
from mongoengine.context_managers import query_counter

from timberjack.fields import ModelField


class ModelFieldDereferenceTestCase(TestCase):
    """
    Test dereferencing ModelField.
    """
    USER_MODEL = get_user_model()

    def setUp(self):
        self.user = self.USER_MODEL.objects.create_user(username='testuser', email='testuser@example.com',
                                                        password='test123.')

    def test_model_instance_dereference(self):

        class TestDocument(Document):
            user = ModelField()
            timestamp = DateTimeField(required=True, default=timezone.now)

        TestDocument.drop_collection()

        document = TestDocument(user=self.user)
        document.save()

        with query_counter() as count:
            self.assertEqual(count, 0)

            instance = TestDocument.objects.order_by('-timestamp').first()
            self.assertEqual(count, 1)

    def test_model_instance_attribute_lookup(self):

        class TestDocument(Document):
            user = ModelField()
            timestamp = DateTimeField(required=True, default=timezone.now)

        TestDocument.drop_collection()

        document = TestDocument(user=self.user)
        document.save()

        instance = TestDocument.objects.first()
        self.assertEqual(instance.user.pk, self.user.pk)
