""" Flask and other extensions instantiated here.

To avoid circular imports with views and create_app(), extensions are
instantiated here. They will be initialized (calling init_app()) in
application.py.
"""
from flask_login import LoginManager
from flask_oauthlib.provider import OAuth2Provider
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CsrfProtect
from injector import singleton

from auth_proxy.injector import InjectorExtension


db = SQLAlchemy()  # pylint: disable=invalid-name
csrf = CsrfProtect()  # pylint: disable=invalid-name
login_manager = LoginManager()  # pylint: disable=invalid-name
oauth = OAuth2Provider()  # pylint: disable=invalid-name

injector = InjectorExtension()  # pylint: disable=invalid-name


def configure(binder):
    """ Add any flask extensions to the injector.
    """
    binder.bind(SQLAlchemy, db, scope=singleton)
    binder.bind(CsrfProtect, csrf, scope=singleton)
    binder.bind(LoginManager, login_manager, scope=singleton)
    binder.bind(OAuth2Provider, oauth, scope=singleton)
