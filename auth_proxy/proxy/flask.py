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

    def __init__(self, url, orig):
        self.url = url
        self.orig = orig

    def request(self):
        """ @inherit
        """
        args = list(self.orig.args.items())

        # We don't care what the client thinks it should be able to see
        args = [arg for arg in args if arg[0] != '_security']

        # Update the query params
        path = self.orig.view_args.get('path').split('/')
        if len(path) == 1:
            args.append(('_security', self._scope_security()))
            args.append(('_security', self._patient_security()))

        # Determine the URL to proxy to
        url = self._create_url(args)

        # Strip out headers that might confuse things
        headers = self._strip_disallowed_headers()

        return {
            'headers': headers,
            'method': self.orig.method,
            'url': url,
            'body': self.orig.data,
        }

    def _create_url(self, args):
        return self.url + '?' + parse.urlencode(args)

    def _strip_disallowed_headers(self):
        return {key: val for (key, val) in self.orig.headers.items()
                   if key in self.allowed_headers}

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

    def _scope_security(self):
        """ Determine which categories the client should be allowed to see
        based on their approved scopes.
        """
        try:
            return ','.join(['public'] + self.orig.oauth.access_token.security_labels)
        except AttributeError:
            return 'public'

    def _patient_security(self):
        """ Determine which Patients the client should be allowed to see.
        """
        try:
            patient = self.orig.oauth.access_token.patient_id
            return 'Patient/{}'.format(patient)
        except AttributeError:
            return 'public'


class OpenFlaskClient(FlaskClient):
    """Subclass of FlaskClient, overridden to prevent any security checks """
    def __init__(self, url, orig):
        super().__init__(url, orig)

    def request(self):
        """
        Creates URL and Headers of redirected request.
        :return: dict of request contents
        """

        url = self._create_url(list(self.orig.args.items()))
        headers = self._strip_disallowed_headers()

        return {
            'headers': headers,
            'method': self.orig.method,
            'url': url,
            'body': self.orig.data,
        }

    def check_request(self):
        """
        Override the base check_request to ignore all security requirements on this request.
        :return: 
        """
        pass
