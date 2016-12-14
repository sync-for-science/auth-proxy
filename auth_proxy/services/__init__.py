# pylint: disable=invalid-name
''' The services module.
'''
from auth_proxy.extensions import db, login_manager, oauthlib
from auth_proxy.services.login import LoginService
from auth_proxy.services.oauth import OAuthService
from auth_proxy.services.proxy import ProxyService


# Create some singletons
login_service = LoginService(db, login_manager)
oauth_service = OAuthService(db, oauthlib)
proxy_service = ProxyService()
