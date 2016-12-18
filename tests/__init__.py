# -*- coding: utf-8 -*-

import os

test_runner = None
old_config = None

os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'

import django
if hasattr(django, 'setup'):
    django.setup()


def setup():
    global test_runner
    global old_config
    from django.test.runner import DiscoverRunner as TestSuiteRunner

    test_runner = TestSuiteRunner()
    test_runner.setup_test_environment()
    old_config = test_runner.setup_databases()


def teardown():
    test_runner.teardown_databases(old_config)
    test_runner.teardown_test_environment()
