""" User module """
from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy_utils.types.password import PasswordType

from auth_proxy.extensions import db


class User(db.Model):
    """ An application User.
    """
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    username = Column(String)
    password = Column(PasswordType(schemes=['pbkdf2_sha512']))

    authenticated = False

    patients = db.relationship('Patient', backref='user')

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

    @property
    def default_patient_id(self):
        """ The default FHIR patient ID for this user.

        If this user is authorized for only one Patient, return that Patient's
        ID. Otherwise, return None.
        """
        if len(self.patients) > 1:
            return None
        return self.patients[0].patient_id

    def patient(self, patient_id):
        """ Return a Patient by patient_id.
        """
        for patient in self.patients:
            if patient_id == patient.patient_id:
                return patient
        return None


class Patient(db.Model):
    """ A Patient associated with a User.
    """
    __tablename__ = 'patient'

    id = Column(Integer, primary_key=True)
    patient_id = Column(String)
    name = Column(String)
    is_user = Column(Boolean)

    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'))
