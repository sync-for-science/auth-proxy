# pylint: disable=missing-docstring
""" Auth Proxy module
"""
from flask import Flask
from flask_injector import FlaskInjector
from flask_oauthlib.provider import OAuth2Provider
from flask_wtf.csrf import CsrfProtect
from injector import Injector
from ordbok.flask_helper import FlaskOrdbok

from auth_proxy.modules import AppModule, ApplicationModule
from auth_proxy import views, cli


def main():
    app = Flask(__name__)

    # Config stuff
    ordbok = FlaskOrdbok(app)
    ordbok.load()
    app.config.update(ordbok)

    # Register CsrfProtect
    csrf = CsrfProtect()
    csrf.init_app(app)

    injector = Injector([AppModule(app), ApplicationModule()])
    views.configure_views(app=app, oauth=injector.get(OAuth2Provider), csrf=csrf)
    cli.configure_views(app=app, injector=injector)

    FlaskInjector(app=app, injector=injector)

    return app
