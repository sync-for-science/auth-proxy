""" User module """
from sqlalchemy import (
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
