# pylint: disable=missing-docstring
""" Modules to bound to injector
"""
from flask_login import LoginManager
from flask_oauthlib.provider import OAuth2Provider
from flask_sqlalchemy import SQLAlchemy
from injector import Module, singleton

from auth_proxy.services import OAuthService, ProxyService, LoginService


class AppModule(Module):
    def __init__(self, app):
        self.app = app

    def configure(self, binder):
        """ We configure the DB here, explicitely, as Flask-SQLAlchemy requires
        the DB to be configured before request handlers are called.
        """
        db = self.configure_db()
        binder.bind(SQLAlchemy, to=db, scope=singleton)
        binder.bind(OAuth2Provider,
                    to=OAuth2Provider(self.app),
                    scope=singleton)
        binder.bind(LoginManager,
                    to=LoginManager(self.app),
                    scope=singleton)

    def configure_db(self):
        return SQLAlchemy(self.app)


class ApplicationModule(Module):
    def configure(self, binder):
        binder.bind(OAuthService, scope=singleton)
        binder.bind(ProxyService)
        binder.bind(LoginService, scope=singleton)

        # Init the singletons
        binder.injector.get(OAuthService)
        binder.injector.get(LoginService)
