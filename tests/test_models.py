# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from timberjack.models import ObjectAccessLog

USER_MODEL = get_user_model()


class ObjectAccessLogTestCase(TestCase):

    def setUp(self):
        self.user = USER_MODEL.objects.create_user(username='test@example.com', password='test123.')
        self.ctype = ContentType.objects.get_for_model(self.user)

    def test_initialize_model(self):
        instance1 = ObjectAccessLog(user_pk=self.user.pk, content_type=self.ctype, object_pk=self.user.pk,
                                    object_repr=repr(self.user), action_flag=4, message='reading user',
                                    level=20)
        instance1.save()
        self.assertIsInstance(instance1, ObjectAccessLog)
