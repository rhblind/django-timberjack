# -*- coding: utf-8 -*-

import re
import os

try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)

setup(
    name='django-timberjack',
    version=get_version('timberjack'),
    description='MongoDB logging system',
    long_description='Store events and stuff in MongoDB',
    author='Rolf Håvard Blindheim',
    author_email='rhblind@gmail.com',
    url='https://gitlab.com/rhblind/django-timberjack',
    download_url='https://gitlab.com/rhblind/django-timberjack.git',
    license='MIT License',
    packages=[
        'timberjack',
    ],
    include_package_data=True,
    install_requires=[
        'Django>=1.8.0',
        'mongoengine>=0.10.6'
    ],
    tests_require=[
        'nose',
        'coverage'
    ],
    zip_safe=False,
    test_suite='tests.runtests.start',
    classifiers=[
        'Operating System :: OS Independent',
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)