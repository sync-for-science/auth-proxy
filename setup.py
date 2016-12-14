#!/usr/bin/env python

from distutils.core import setup

setup(
    name='AuthProxy',
    version='1.0.0',
    packages=['auth_proxy'],
    install_requires=[
        'arrow',
        'flask',
        'Flask-Login',
        'Flask_OAuthlib',
        'Flask-SQLAlchemy',
        'Flask-WTF',
        'furl',
        'passlib',
        'pep8',
        'pylint',
        'pytest',
        'PyYaml',
        'requests',
        'SQLAlchemy',
        'SQLAlchemy-Utils',
        'uwsgi',
    ],
)
