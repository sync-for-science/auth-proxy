# pylint: disable=invalid-name
""" Flask and other extensions instantiated here.

To avoid circular imports with views and create_app(), extensions are
instantiated here. They will be initialized (calling init_app()) in
application.py.
"""
from auth_proxy.oauth2 import PatchedOAuth2Provider
from flask_cors import CORS
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CsrfProtect


db = SQLAlchemy()
csrf = CsrfProtect()
login_manager = LoginManager()
oauthlib = PatchedOAuth2Provider()
cors = CORS()
