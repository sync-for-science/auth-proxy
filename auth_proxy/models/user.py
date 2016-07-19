""" User module """
from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
)

from . import Base


class User(Base):
    """ An application User.
    TODO: see if this is even necessary.
    """
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    patient_id = Column(String)
    username = Column(String)
    password = Column(String)
    authenticated = Column(Boolean, default=False)

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
        """ False, as anonymouse users aren't supported.
        """
        return False
