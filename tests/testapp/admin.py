# -*- coding: utf-8 -*-

from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin

from timberjack.admin import TimberjackMixin

admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(TimberjackMixin, UserAdmin):
    pass


@admin.register(Group)
class GroupAdmin(TimberjackMixin, GroupAdmin):
    pass

