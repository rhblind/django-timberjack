# -*- coding: utf-8 -*-

from django.conf.urls import include, url
from django.contrib.auth.models import User
from django.test import override_settings
from rest_framework import status
from rest_framework.reverse import reverse

from rest_framework.test import APITestCase
from rest_framework.routers import DefaultRouter
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from timberjack.documents import ObjectAccessLog, READ, CREATE, UPDATE, DELETE
from timberjack.compat.rest_framework import mixins


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class UserViewSet(mixins.AccessLogModelViewMixin, ModelViewSet):
    write_admin_log = True
    serializer_class = UserSerializer
    queryset = User.objects.all()


router = DefaultRouter()
router.register(r'users', viewset=UserViewSet)
urlpatterns = [
    url(r'^', include(router.urls))
]


@override_settings(ROOT_URLCONF='tests.test_rest_framework_mixin')
class AccessLogModelViewMixinTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'testuser@example.com', 'test123.')
        self.client.login(username=self.user.username, password='test123.')

    def test_get_object_is_logged(self):
        response = self.client.get(reverse('user-detail', kwargs={'pk': self.user.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        instance = ObjectAccessLog.objects.filter(action_flag=READ).order_by('-timestamp').first()
        self.assertEqual(instance.get_content_object(), self.user)

    def test_post_object_is_logged(self):
        response = self.client.post(reverse('user-list'), data={
            'username': 'another-user',
            'email': 'another-user@example.com',
            'password': 'test123.'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        instance = ObjectAccessLog.objects.filter(action_flag=CREATE).order_by('-timestamp').first()
        self.assertEqual(instance.get_content_object(), User.objects.get(username='another-user'))

    def test_patch_object_is_logged(self):
        response = self.client.patch(reverse('user-detail', kwargs={'pk': self.user.pk}), data={
            'username': 'changed-user'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        instance = ObjectAccessLog.objects.filter(action_flag=UPDATE).order_by('-timestamp').first()
        self.assertEqual(instance.get_content_object(), self.user)

    def test_put_object_is_logged(self):
        response = self.client.put(reverse('user-detail', kwargs={'pk': self.user.pk}), data={
            'username': 'changed-user',
            'email': 'changed-user@example.com',
            'password': 'test123.'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        instance = ObjectAccessLog.objects.filter(action_flag=UPDATE).order_by('-timestamp').first()
        self.assertEqual(instance.get_content_object(), self.user)

    def test_delete_object_is_logged(self):
        user = User.objects.create_user('delete-me', 'delete-me@example.com', 'test123.')
        response = self.client.delete(reverse('user-detail', kwargs={'pk': user.pk}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        instance = ObjectAccessLog.objects.filter(action_flag=DELETE).order_by('-timestamp').first()
        try:
            instance.get_content_object()
            self.fail('Did not fail when trying to get deleted instance')
        except User.DoesNotExist as e:
            self.assertEqual(str(e), 'User matching query does not exist.')
