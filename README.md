# django-timberjack

[![Build Status](https://travis-ci.org/rhblind/django-timberjack.svg?branch=master)](https://travis-ci.org/rhblind/django-timberjack)
[![Coverage Status](https://coveralls.io/repos/github/rhblind/django-timberjack/badge.svg?branch=master)](https://coveralls.io/github/rhblind/django-timberjack?branch=master)

Write logs to MongoDB.

**BIG FAT WARNING**

Probably not a very good choice for storing logs, so consider this an experimental project 
I'll probably abandon once I've got a better solution.


## Setup

Set up Mongo connections in `settings.py`

```
MONGO_CONNECTIONS = {
    'default': {
        'NAME': 'default',  # Hostname or URI. If using URI, it will override all other options.
        'HOST': os.environ.get('MONGO_HOST', 'localhost')
    }
}
```

## Usage

The project contains a single document definition `timberjack.documents.ObjectAccessLog`.
Use this to write object access log entries and optionally write a `admin.LogEntry` entry for the
same record.
