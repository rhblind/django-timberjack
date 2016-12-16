# -*- coding: utf-8 -*-

from django.apps import AppConfig

from . import connections


class TimberJackConfig(AppConfig):
    name = 'timberjack'
    label = 'timberjack'

    def ready(self):
        """
        Reload all mongo connections.
        """
        connections.reload_all()
