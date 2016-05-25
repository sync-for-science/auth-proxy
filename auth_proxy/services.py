""" Services module.
"""
from datetime import datetime, timedelta
import uuid

from flask_oauthlib.provider import OAuth2Provider
from flask_sqlalchemy import SQLAlchemy
from injector import inject
import requests

from auth_proxy.models.oauth import Client, Grant, Token
from auth_proxy.proxy import Proxy
from auth_proxy.proxy.flask import FlaskClient
from auth_proxy.proxy.requests import RequestsServer


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

    def register(self, client_id, redirect_uris, scopes):
        """ Register new clients.
        """
        client = Client(
            client_id=client_id,
            client_secret=str(uuid.uuid4()),
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

    def cb_clientgetter(self, client_id):
        """ OAuth2Provider Client getter.
        """
        return self.db.session.query(Client).\
            filter_by(client_id=client_id).first()

    def cb_grantgetter(self, client_id, code):
        """ OAuth2Provider Grant getter.
        """
        return self.db.session.query(Grant).\
            filter_by(client_id=client_id, code=code).first()

    def cb_grantsetter(self, client_id, code, request, *args, **kwargs):
        """ OAuth2Provider Grant setter.
        """
        expires = datetime.utcnow() + timedelta(seconds=100)
        grant = Grant(
            client_id=client_id,
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
        """
        tokens = self.db.session.query(Token).\
            filter_by(client_id=request.client.client_id)

        # Make sure that every client has only one token.
        for old in tokens:
            self.db.session.delete(old)

        expires_in = token.get('expires_in')
        expires = datetime.utcnow() + timedelta(seconds=expires_in)

        new = Token(
            access_token=token['access_token'],
            refresh_token=token['refresh_token'],
            token_type=token['token_type'],
            _scopes=token['scope'],
            expires=expires,
            client_id=request.client.client_id,
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
