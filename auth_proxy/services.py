""" Services module.
"""
from datetime import datetime, timedelta
import uuid

import flask_login
from flask_oauthlib.provider import OAuth2Provider
from flask_sqlalchemy import SQLAlchemy
from injector import inject
import requests

from auth_proxy.models.oauth import Client, Grant, Token
from auth_proxy.models.user import User
from auth_proxy.proxy import Proxy
from auth_proxy.proxy.flask import FlaskClient
from auth_proxy.proxy.requests import RequestsServer


class LoginService(object):
    """ Handle all our login operations.
    """
    @inject(db=SQLAlchemy, login_manager=flask_login.LoginManager)
    def __init__(self, db, login_manager):
        self.db = db
        self.login_manager = login_manager

        login_manager.login_view = 'login'
        login_manager.user_loader(self.load_user)

    def load_user(self, user_id):
        """ LoginManager user_loader callback.
        """
        user = self.db.session.query(User).\
            filter_by(id=user_id).first()

        return user

    def log_in_user(self, username, password):
        """ Handle the login process.
        """
        user = self.db.session.query(User).\
            filter_by(username=username).first()

        assert user, 'User not found.'
        assert user.password == password, 'Incorrect password.'

        flask_login.login_user(user)

    def log_out_user(self):
        """ Handle the logout process.
        """
        flask_login.logout_user()


class OAuthService(object):
    """ Handle all our oAuth operations.
    """
    @inject(db=SQLAlchemy, oauth=OAuth2Provider)
    def __init__(self, db, oauth):
        self.db = db
        self.oauth = oauth

        oauth.clientgetter(self.cb_clientgetter)
        oauth.grantgetter(self.cb_grantgetter)
        oauth.grantsetter(self.cb_grantsetter)
        oauth.tokengetter(self.cb_tokengetter)
        oauth.tokensetter(self.cb_tokensetter)

    def register(self, client_id, redirect_uris, scopes, client_secret=None):
        """ Register new clients.
        """
        if client_secret is None:
            client_secret = str(uuid.uuid4())

        client = Client(
            client_id=client_id,
            client_secret=client_secret,
            _redirect_uris=redirect_uris,
            _default_scopes=scopes,
        )
        self.db.session.add(client)
        self.db.session.commit()

        return {
            'client_id': client.client_id,
            'client_secret': client.client_secret,
            'redirect_uris': client.redirect_uris,
            'default_scopes': client.default_scopes,
        }

    def audit(self, client_id):
        """ Audit all the tokens available to a client.
        """
        return self.db.session.query(Token).\
            filter_by(client_id=client_id)

    def authorizations(self):
        """ Audit all the tokens authorized for a User.
        """
        user = flask_login.current_user

        return self.db.session.query(Token).\
            filter_by(user_id=user.id)

    def revoke_token(self, token_id):
        """ Revoke an authorized token.
        """
        self.db.session.query(Token).\
            filter_by(id=token_id).\
            delete()
        self.db.session.commit()

    def show_authorize_prompt(self, client_id):
        """ Provide everything necessary to show the authorize prompt.
        """
        client = self.db.session.query(Client).\
            filter_by(client_id=client_id).first()

        return client

    def smart_token_credentials(self, grant_type, code=None, refresh_token=None):
        """ Provide additional credentials required by a SMART token request.
        """
        if grant_type == 'authorization_code':
            grant = self.db.session.query(Grant).\
                filter_by(code=code).first()
            user = getattr(grant, 'user', None)
        elif grant_type == 'refresh_token':
            token = self.db.session.query(Token).\
                filter_by(refresh_token=refresh_token).first()
            user = getattr(token, 'user', None)
        else:
            user = None

        if user is None:
            return None

        return {
            'patient': user.patient_id,
        }

    def cb_clientgetter(self, client_id):
        """ OAuth2Provider Client getter.
        """
        return self.db.session.query(Client).\
            filter_by(client_id=client_id).first()

    def cb_grantgetter(self, client_id, code):
        """ OAuth2Provider Grant getter.
        """
        now = datetime.now()

        grant = self.db.session.query(Grant).filter(
            Grant.client_id == client_id,
            Grant.code == code,
            Grant.expires >= now,
        ).first()

        if grant:
            grant.session = self.db.session

        return grant

    def cb_grantsetter(self, client_id, code, request, *args, **kwargs):
        """ OAuth2Provider Grant setter.
        """
        expires = datetime.utcnow() + timedelta(seconds=100)
        user = self.db.session.query(User).\
            filter_by(id=1).first()

        assert user is not None

        grant = Grant(
            client_id=client_id,
            user=user,
            code=code['code'],
            redirect_uri=request.redirect_uri,
            _scopes=' '.join(request.scopes),
            expires=expires
        )

        self.db.session.add(grant)
        self.db.session.commit()

        return grant

    def cb_tokengetter(self, access_token=None, refresh_token=None):
        """ OAuth2Provider Token getter.
        """
        if access_token:
            return self.db.session.query(Token).\
                filter_by(access_token=access_token).first()
        elif refresh_token:
            return self.db.session.query(Token).\
                filter_by(refresh_token=refresh_token).first()

    def cb_tokensetter(self, token, request, *args, **kwargs):
        """ OAuth2Provider Token setter.

        Parameters:
            token : dict
            request : oauthlib.Request
        """
        tokens = self.db.session.query(Token).\
            filter_by(client_id=request.client.client_id)

        # Make sure that every client has only one token.
        for old in tokens:
            self.db.session.delete(old)

        expires_in = token.get('expires_in')
        expires = datetime.utcnow() + timedelta(seconds=expires_in)

        assert request.user is not None

        new = Token(
            access_token=token['access_token'],
            refresh_token=token['refresh_token'],
            token_type=token['token_type'],
            _scopes=token['scope'],
            expires=expires,
            client_id=request.client.client_id,
            user=request.user,
        )
        self.db.session.add(new)
        self.db.session.commit()

        return new


class ProxyService(object):
    """ Handle proxying the FHIR API.
    """
    def conformance(self, url, authorize=None, token=None, register=None):
        """ Proxy the conformance statement.
        We need to set the oAuth uris extension though.
        """
        headers = {
            'Accept': 'application/json+fhir',
        }
        response = requests.get(url, headers=headers)
        conformance = response.json()

        extension = {
            'url': 'http://fhir-registry.smarthealthit.org/StructureDefinition/oauth-uris',
            'extension': [],
        }

        if authorize is not None:
            extension['extension'].append({
                'url': 'authorize',
                'valueUri': authorize,
            })

        if token is not None:
            extension['extension'].append({
                'url': 'token',
                'valueUri': token,
            })

        if register is not None:
            extension['extension'].append({
                'url': 'register',
                'valueUri': register,
            })

        security = conformance['rest'][0].get('security', {})
        security['extension'] = [extension]
        conformance['rest'][0]['security'] = security

        return conformance

    def api(self, url, request):
        """ Proxy FHIR API requests.
        """
        client = FlaskClient(url, request)
        server = RequestsServer()
        proxy = Proxy(client, server)

        return proxy.proxy()
