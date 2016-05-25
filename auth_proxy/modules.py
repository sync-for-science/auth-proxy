# pylint: disable=missing-docstring
""" Modules to bound to injector
"""
from flask_oauthlib.provider import OAuth2Provider
from flask_sqlalchemy import SQLAlchemy
from injector import Module, singleton

from auth_proxy.services import OAuthService


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

        @self.app.before_first_request
        def cb_create_database(*args, **kwargs):  # pylint: disable=unused-variable
            from auth_proxy.models import Base, oauth
            Base.metadata.create_all(db.engine)
            db.session.commit()

    def configure_db(self):
        return SQLAlchemy(self.app)


class ApplicationModule(Module):
    def configure(self, binder):
        binder.bind(OAuthService, scope=singleton)
