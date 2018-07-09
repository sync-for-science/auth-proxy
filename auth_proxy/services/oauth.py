""" OAuth Service module.
"""
from datetime import datetime, timedelta
from urllib.parse import urlparse
import uuid

import arrow
import flask_login

from auth_proxy.models.oauth import Client, Grant, Token
from auth_proxy.models.user import User


class OAuthServiceError(Exception):
    """Some error occured with the OAuth service."""
    def __init__(self, error, description=None):
        self.error = error
        self.description = description or error


class OAuthService(object):
    """ Handle all our oAuth operations.
    """
    def __init__(self, db, oauth):
        self.db = db
        self.oauth = oauth

        oauth.clientgetter(self.cb_clientgetter)
        oauth.grantgetter(self.cb_grantgetter)
        oauth.grantsetter(self.cb_grantsetter)
        oauth.tokengetter(self.cb_tokengetter)
        oauth.tokensetter(self.cb_tokensetter)

    def register(self, redirect_uris, scopes, client_name=None):
        """ Register new clients. See RFC7591.
        """

        if not redirect_uris:
            raise OAuthServiceError(
                'invalid_client_metadata',
                'One or more redirect URIs are required.'
            )

        for uri in redirect_uris:
            validate_redirect_uri(uri)

        # TODO: validate scopes?

        client_id = str(uuid.uuid4())
        client_secret = str(uuid.uuid4())

        if client_name is None:
            client_name = client_id

        client = Client(
            client_id=client_id,
            client_secret=client_secret,
            name=client_name,
            _redirect_uris=' '.join(redirect_uris),
            _default_scopes=scopes,
            _security_labels=' '.join([
                'patient',
                'medications',
                'allergies',
                'immunizations',
                'problems',
                'procedures',
                'vital-signs',
                'laboratory',
                'smoking',
            ]),
        )
        self.db.session.add(client)
        self.db.session.commit()

        return {
            'client_id': client.client_id,
            'client_secret': client.client_secret,
            'client_secret_expires_at': 0,  # never
            'client_name': client.name,
            'redirect_uris': client.redirect_uris,
            'scope': ' '.join(client.default_scopes),
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
            token = self.db.session.query(Token).\
                filter_by(client=grant.client).\
                filter_by(user=grant.user).\
                first()
        elif grant_type == 'refresh_token':
            token = self.db.session.query(Token).\
                filter_by(refresh_token=refresh_token).first()
        else:
            return False

        if not token:
            return False

        return {
            'patient': token.patient_id,
        }

    def create_authorization(self, client_id, expires, security_labels, user, patient_id):
        """ Creates the initial authorization token.
        """
        old = self.db.session.query(Token).\
            filter_by(client_id=client_id).\
            all()
        for token in old:
            self.db.session.delete(token)

        token = Token(
            client_id=client_id,
            user=user,
            approval_expires=arrow.get(expires).datetime,
            _security_labels=security_labels,
            patient_id=patient_id,
        )

        self.db.session.add(token)
        self.db.session.commit()

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
        user = flask_login.current_user

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

        Retrieve all unexpired tokens, and update the one with the latest
        approval expiration time; delete the remainder. See
        https://github.com/sync-for-science/auth-proxy/issues/45 for details.
        """
        assert request.user is not None

        today = arrow.now().datetime

        old_tokens = self.db.session.query(Token).\
            filter_by(client_id=request.client.client_id).\
            filter(Token.approval_expires >= today).\
            order_by(Token.approval_expires)

        # use the token with latest approval expires date
        new = old_tokens[-1].refresh(**token)

        for old in old_tokens:
            self.db.session.delete(old)

        self.db.session.add(new)
        self.db.session.commit()

        return new

    def create_debug_token(self, client_id, access_lifetime, approval_expires, scopes, user, patient_id):

        if not user:
            raise OAuthServiceError(
                'no_user',
                '"username" is required.'
            )

        creating_user = User.query.filter_by(username=user).first()
        if not creating_user:
            raise OAuthServiceError(
                'no_user',
                'Username "{}" not found'.format(user)
            )

        if not client_id:
            raise OAuthServiceError(
                'no_client',
                '"client_id" is required.'
            )

        client = Client.query.filter_by(client_id=client_id).first()
        if not client:
            raise OAuthServiceError(
                'no_client',
                'Client ID "{}" not found.'.format(client_id)
            )

        if not patient_id:
            raise OAuthServiceError(
                'no_patient',
                '"patient_id" is required.'
            )

        # ensure the patient belongs to the user
        if not creating_user.patient(patient_id):
            raise OAuthServiceError(
                'no_patient_for_user',
                'Patient ID "{}" does not belong to user "{}"'.format(patient_id, user)
            )

        try:
            access_lifetime = int(access_lifetime)
        except ValueError:
            raise OAuthServiceError(
                'malformed_lifetime',
                'Access token lifetime should be an integer.'
            )

        try:
            approval_expires = datetime.fromtimestamp(int(approval_expires))
        except ValueError:
            raise OAuthServiceError(
                'malformed_expiration',
                'Approval expiration time should be a Unix timestamp.'
            )

        if scopes is None:
            scopes = ' '.join(client.default_scopes)

        token = Token(
            client_id=client_id,
            client=client,
            approval_expires=approval_expires,
            _scopes=scopes,
            user=creating_user,
            patient_id=patient_id
        )

        self.db.session.add(token)
        self.db.session.commit()

        generated_access_token = str(uuid.uuid4())
        generated_refresh_token = str(uuid.uuid4())

        # We want to keep the debug token generation as close to the real authorization process as possible.
        # To that end we use the refresh method on the token object to set access/refresh tokens and expiry.
        new = token.refresh(generated_access_token,
                            generated_refresh_token,
                            access_lifetime,
                            "Bearer",
                            scopes)

        self.db.session.delete(token)
        self.db.session.add(new)
        self.db.session.commit()

        return new


def validate_redirect_uri(uri):
    result = urlparse(uri)

    if not result.scheme:
        raise OAuthServiceError(
            'invalid_redirect_uri',
            'A URI scheme is required: {}'.format(uri)
        )

    if result.fragment:
        raise OAuthServiceError(
            'invalid_redirect_uri',
            'URI fragments are disallowed in redirect URIs: {}'.format(uri)
        )
