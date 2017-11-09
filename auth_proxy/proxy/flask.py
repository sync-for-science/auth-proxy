""" Flask specific implementation of Proxy.
"""
from urllib import parse

from . import Client, ForbiddenError


class FlaskClient(Client):
    """ Converts a Flask request object into a generic one.
    """
    allowed_headers = ['Accept', 'Origin']
    allowed_args = [
        '_count',
        '_format',
        '_lastUpdated',
        'category',
        'patient',
        '_security',
        'beneficiary'
    ]
    allowed_methods = ['GET']
    allowed_resources = [
        'metadata',
        'AllergyIntolerance',
        'Binary',
        'Condition',
        'Coverage',
        'DocumentReference',
        'Encounter',
        'ExplanationOfBenefit',
        'Immunization',
        'MedicationAdministration',
        'MedicationDispense',
        'MedicationStatement',
        'MedicationRequest',
        'Observation',
        'Patient',
        'Practitioner',
        'Procedure',
    ]

    SECURITY_ARG_NAME = '_security'

    def __init__(self, url, orig):
        self.url = url
        self.orig = orig

    def request(self):
        """ @inherit
        """

        args = list(self.orig.args.items())

        path = self.orig.view_args.get('path').split('/')

        if len(path) == 1:
            args = self._get_secure_args(args)

        headers = {key: val for (key, val) in self.orig.headers.items()
                            if key in self.allowed_headers}

        return {
            'headers': headers,
            'method': self.orig.method,
            'url': self.url + '?' + parse.urlencode(args),
            'body': self.orig.data,
        }

    def _get_secure_args(self, original_args):
        """
        Strip existing security arguments and apply our own.
        :param original_args: 
        :return: list: new request arguments with injected security
        """
        stripped_args = [arg for arg in original_args if arg[0] != self.SECURITY_ARG_NAME]

        stripped_args.append((self.SECURITY_ARG_NAME, self._get_scope_security_label()))
        stripped_args.append((self.SECURITY_ARG_NAME, self._get_patient_security_label()))

        return stripped_args

    def check_request(self):
        """ @inherit
        """
        for key in self.orig.args:
            if key not in self.allowed_args:
                raise ForbiddenError(parameter=key)

        if self.orig.method not in self.allowed_methods:
            raise ForbiddenError(method=self.orig.method)

        path = self.orig.view_args.get('path').split('/')[0]

        if path not in self.allowed_resources:
            raise ForbiddenError(segment=path)

    def _get_scope_security_label(self):
        """ Determine which categories the client should be allowed to see
        based on their approved scopes.
        """
        try:
            labels = ','.join(['public'] + self.orig.oauth.access_token.security_labels)
        except AttributeError:
            labels = 'public'
        return labels

    def _get_patient_security_label(self):
        """ Determine which Patients the client should be allowed to see.
        """
        try:
            patient = self.orig.oauth.access_token.patient_id
            labels = 'Patient/{}'.format(patient)
        except AttributeError:
            labels = 'public'
        return labels


class UnsecureFlaskClient(FlaskClient):
    """Subclass of FlaskClient, overridden to prevent any security checks """

    def _get_secure_args(self, original_args):
        return original_args
