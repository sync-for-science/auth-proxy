""" OAuth Service module.
"""
from datetime import datetime, timedelta
import uuid

import flask_login
from flask_oauthlib.provider import OAuth2Provider
from flask_sqlalchemy import SQLAlchemy
from injector import inject

from auth_proxy.models.oauth import Client, Grant, Token
from auth_proxy.models.user import User


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

        return self.db.session.query(Grant).filter(
            Grant.client_id == client_id,
            Grant.code == code,
            Grant.expires >= now,
        ).first()

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


def configure(binder):
    """ Configure this module for the Injector.
    """
    binder.bind(OAuthService)