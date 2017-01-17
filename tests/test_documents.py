# -*- coding: utf-8 -*-

from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from timberjack.documents import LOG_LEVEL, ObjectAccessLog

USER_MODEL = get_user_model()


class ObjectAccessLogConstantsTestCase(TestCase):

    def test_crud_action_values(self):
        self.assertEqual(ObjectAccessLog.CREATE_ACTION, 1)
        self.assertEqual(ObjectAccessLog.UPDATE_ACTION, 2)
        self.assertEqual(ObjectAccessLog.DELETE_ACTION, 3)
        self.assertEqual(ObjectAccessLog.READ_ACTION, 4)

    def test_crud_action_values_django_compatibility(self):
        self.assertEqual(ObjectAccessLog.CREATE_ACTION, ADDITION)
        self.assertEqual(ObjectAccessLog.UPDATE_ACTION, CHANGE)
        self.assertEqual(ObjectAccessLog.DELETE_ACTION, DELETION)

    def test_log_level_values(self):
        log_levels = ['NOTSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        for i, values in enumerate(LOG_LEVEL):
            num, value = values
            self.assertEqual(i * 10, num)
            self.assertEqual(value, log_levels[i])


class ObjectAccessLogTestCase(TestCase):

    def setUp(self):
        self.user = USER_MODEL.objects.create_user(username='test@example.com', password='test123.')
        self.ctype = ContentType.objects.get_for_model(self.user)

    def test_document_initialize(self):
        instance = ObjectAccessLog(user=self.user, content_type=self.ctype, object_pk=self.user.pk,
                                   object_repr=repr(self.user), action_flag=1, message='test message')
        self.assertIsInstance(instance, ObjectAccessLog)

    def test_document_properties(self):
        instance = ObjectAccessLog(user=self.user, content_type=self.ctype, object_pk=self.user.pk,
                                   object_repr=repr(self.user), action_flag=1, message='test message')
        self.assertTrue(instance.is_create_action)

        instance.action_flag = 2
        self.assertTrue(instance.is_update_action)

        instance.action_flag = 3
        self.assertTrue(instance.is_delete_action)

        instance.action_flag = 4
        self.assertTrue(instance.is_read_action)

    def test_document_get_log_message(self):
        instance = ObjectAccessLog(user=self.user, content_type=self.ctype, object_pk=self.user.pk,
                                   object_repr=repr(self.user), action_flag=1, message='test message')
        self.assertEqual(instance.get_log_message(), 'test message')

        instance.message = ''
        self.assertEqual(instance.get_log_message(), '')

    def test_document_write_admin_log(self):
        instance = ObjectAccessLog(user=self.user, content_type=self.ctype, object_pk=self.user.pk,
                                   object_repr=repr(self.user), action_flag=1, message='test message')
        instance.save(write_admin_log=True)

        self.assertIsInstance(instance.get_admin_log_object(), LogEntry)
        self.assertEqual(instance.get_admin_log_object(), LogEntry.objects.get(pk=instance.admin_log_pk))

    def test_document_referrer(self):
        instance1 = ObjectAccessLog(user=self.user, content_type=self.ctype, object_pk=self.user.pk,
                                    object_repr=repr(self.user), action_flag=1, message='message 1')
        instance1.save()

        instance2 = ObjectAccessLog(user=self.user, content_type=self.ctype, object_pk=self.user.pk,
                                    object_repr=repr(self.user), action_flag=1, message='message 2',
                                    referrer=instance1)
        instance2.save()

        self.assertEqual(instance1, instance2.referrer)


class ObjectAccessQuerySetTestCase(TestCase):

    def setUp(self):
        self.user = USER_MODEL.objects.create_user(username='test@example.com', password='test123.')
        self.ctype = ContentType.objects.get_for_model(self.user)

    def test_queryset_log_action(self):
        instance = ObjectAccessLog.objects.log_action(user=self.user, content_type=self.ctype,
                                                      object_pk=self.user.pk, object_repr=repr(self.user),
                                                      action_flag=1, message='test message')
        self.assertIsInstance(instance, ObjectAccessLog)
