# -*- coding: utf-8 -*-

from django.conf.urls import url
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings

from django.views.generic import CreateView, UpdateView, DeleteView, DetailView


class CreateUserView(CreateView):
    model = User
    fields = '__all__'


class UpdateUserView(UpdateView):
    model = User
    fields = '__all__'


class DeleteUserView(DeleteView):
    model = User


class DetailUserView(DetailView):
    model = User
    fields = '__all__'


urlpatterns = [
    url(r'^create-user/$', view=CreateUserView.as_view(), name='create-user'),
    url(r'^update-user/(?P<pk>\d+)/$', view=UpdateUserView.as_view(), name='update-user'),
    url(r'^delete-user/(?P<pk>\d+)/$', view=DeleteUserView.as_view(), name='delete-user'),
    url(r'^detail-user/(?P<pk>\d+)/$', view=DetailUserView.as_view(), name='detail-user')
]


@override_settings(ROOT_URLCONF='tests.test_django_forms_mixin')
class AccessLogModelFormMixinTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'testuser@example.com', 'test123.')
        self.client.login(username=self.user.username, password='test123.')

    def test_create_view_object_is_logged(self):
        response = self.client.post(reverse('create-user'), data={
            'username': 'another-user',
            'email': 'another-user@example.com',
            'password': 'test123.'
        })
        self.assertEqual(response.status_code, 200)

    def test_detail_view_object_is_logged(self):
        response = self.client.get(reverse('detail-user', kwargs={'pk': self.user.pk}))
        self.assertEqual(response.status_code, 200)
