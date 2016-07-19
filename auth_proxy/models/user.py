""" User module """
from sqlalchemy import (
    Column,
    Integer,
    String,
)
from sqlalchemy_utils.types.password import PasswordType

from . import Base


class User(Base):
    """ An application User.
    TODO: see if this is even necessary.
    """
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    patient_id = Column(String)
    username = Column(String)
    password = Column(PasswordType(schemes=['pbkdf2_sha512']))

    authenticated = False

    def is_active(self):
        """ True, as all users are active.
        """
        return True

    def get_id(self):
        """ Return the user id.
        """
        return str(self.id)

    def is_authenticated(self):
        """ Return True if the user is authenticated.
        """
        return self.authenticated

    def is_anonymous(self):
        """ False, as anonymous users aren't supported.
        """
        return False
