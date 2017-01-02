# -*- coding: utf-8 -*-

from mongoengine.connection import DEFAULT_CONNECTION_NAME

DEFAULT_ALIAS = DEFAULT_CONNECTION_NAME  # pragma: no cover

# We want to log CRUD actions.
# (keep numerical values compatible with admin.LogEntry model)
CREATE = 1
UPDATE = 2
DELETE = 3
READ = 4
