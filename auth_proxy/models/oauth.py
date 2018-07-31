# pylint: disable=missing-docstring
""" oAuth models module """
from datetime import datetime, timedelta

from sqlalchemy import (
    Column,
    ForeignKey,
    DateTime,
    Integer,
    String,
    Text,
    orm
)

from auth_proxy.extensions import db


class Client(db.Model):
    """ A client is the app which want to use the resource of a user.
    """
    __tablename__ = 'client'

    client_id = Column(String, primary_key=True)
    client_secret = Column(String, nullable=False)
    name = Column(String, nullable=False)

    _redirect_uris = Column('redirect_uris', Text)
    _default_scopes = Column('default_scopes', Text)
    _security_labels = Column('security_labels', Text)

    @property
    def client_type(self):
        return 'confidential'

    @property
    def redirect_uris(self):
        if self._redirect_uris:
            return self._redirect_uris.split()
        return []

    @property
    def default_redirect_uri(self):
        return self.redirect_uris[0]

    @property
    def default_scopes(self):
        if self._default_scopes:
            return self._default_scopes.split()
        return []

    @property
    def security_labels(self):
        if self._security_labels:
            return self._security_labels.split()
        return []


class Grant(db.Model):
    """ A grant token is created in the authorization flow, and will be
    destroyed when the authorization finished.
    """
    __tablename__ = 'grant'

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'))
    user = orm.relationship('User')

    client_id = Column(String, ForeignKey('client.client_id'),
                       nullable=False)
    client = orm.relationship('Client')

    code = Column(String, index=True, nullable=False)

    redirect_uri = Column(String)
    expires = Column(DateTime)

    _scopes = Column('scopes', Text)

    def delete(self):
        self.expires = datetime.now()
        # This is not ideal, but FlaskOauth forces it on us
        db.session.commit()

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []


class Token(db.Model):
    """ A bearer token is the final token that could be used by the client.
    There are other token types, but bearer token is widely used.
    """
    __tablename__ = 'token'

    id = Column(Integer, primary_key=True)

    client_id = Column(String, ForeignKey('client.client_id'),
                       nullable=False)
    client = orm.relationship('Client')

    user_id = Column(Integer, ForeignKey('user.id'))
    user = orm.relationship('User')

    # currently only bearer is supported
    token_type = Column(String)

    access_token = Column(String, unique=True)
    refresh_token = Column(String, unique=True)
    expires = Column(DateTime)  # access token expiration time
    approval_expires = Column(DateTime)  # refresh token expiration time
    _scopes = Column('scopes', Text)
    _security_labels = Column('security_labels', Text)

    # FHIR Patient id
    patient_id = Column(String, ForeignKey('patient.patient_id'),
                        nullable=False)
    patient = orm.relationship('Patient')

    def refresh(self, access_token, refresh_token, expires_in, token_type, scope, **kwargs):
        expires = datetime.utcnow() + timedelta(seconds=expires_in)

        return Token(
            client=self.client,
            user=self.user,
            approval_expires=self.approval_expires,
            _security_labels=self._security_labels,
            patient_id=self.patient_id,
            token_type=token_type,
            access_token=access_token,
            refresh_token=refresh_token,
            expires=expires,
            _scopes=scope,
        )

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []

    @property
    def security_labels(self):
        if self._security_labels:
            return self._security_labels.split()
        return []

    @property
    def interest(self):

        return {
            'token_type': self.token_type,
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'approval_expires': self.approval_expires,
            'security_labels': self.security_labels,
            'access_expires': self.expires,
            'scope': ' '.join(self.scopes),
            'client_id': self.client.client_id,
            'username': self.user.username
        }
