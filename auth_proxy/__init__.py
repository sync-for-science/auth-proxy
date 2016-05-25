# pylint: disable=missing-docstring
""" Auth Proxy module
"""
from flask import Flask
from flask_injector import FlaskInjector
from flask_oauthlib.provider import OAuth2Provider
from injector import Injector

from auth_proxy.modules import AppModule, ApplicationModule
from auth_proxy.services import OAuthService
from auth_proxy.views import configure_views


def main():
    app = Flask(__name__)
    app.debug = True
    app.config.update(
        SQLALCHEMY_DATABASE_URI='sqlite:///db.sqlite',
    )

    injector = Injector([AppModule(app), ApplicationModule()])
    injector.get(OAuthService)  # Hacky, but we need to init the singleton
    configure_views(app=app, oauth=injector.get(OAuth2Provider))

    FlaskInjector(app=app, injector=injector)

    return app
