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
    ]
    allowed_methods = ['GET']
    allowed_resources = [
        'metadata',
        'AllergyIntolerance',
        'Binary',
        'Condition',
        'DocumentReference',
        'Encounter',
        'Immunization',
        'MedicationAdministration',
        'MedicationDispense',
        'MedicationOrder',
        'MedicationStatement',
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

        stripped_args, stripped_headers = self._get_secured_args_and_headers()

        return {
            'headers': stripped_headers,
            'method': self.orig.method,
            'url': self._create_url(stripped_args),
            'body': self.orig.data,
        }

    def _get_secured_args_and_headers(self):
        """
        Enforce security on the request by removing existing security parameters and 
        adding our own based on scope/patient authorizations. Also remove headers 
        not in the allowed list.
        :return: list, dict : The modified request arguments and headers.
        """

        original_args = list(self.orig.args.items())

        # Strip existing security arguments so we can apply our own.
        stripped_args = [arg for arg in original_args if arg[0] != self.SECURITY_ARG_NAME]

        # Add security based on the requested path.
        path = self.orig.view_args.get('path').split('/')

        if len(path) == 1:
            stripped_args.append((self.SECURITY_ARG_NAME, self._get_scope_security_label()))
            stripped_args.append((self.SECURITY_ARG_NAME, self._get_patient_security_label()))

        # Remove headers based on a list of allowed ones.
        stripped_headers = {key: val for (key, val) in self.orig.headers.items()
                            if key in self.allowed_headers}

        return stripped_args, stripped_headers

    def _create_url(self, args):
        return self.url + '?' + parse.urlencode(args)

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

    def request(self):
        """
        Ignore all security checks and pass the request through.
        :return: 
        """

        return {
            'headers': {key: val for (key, val) in self.orig.headers.items()},
            'method': self.orig.method,
            'url': self._create_url(list(self.orig.args.items())),
            'body': self.orig.data,
        }