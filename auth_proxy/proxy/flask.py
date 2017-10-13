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
        original_args = list(self.orig.args.items())

        # We don't care what the client thinks it should be able to see
        stripped_args = self._strip_security_args(original_args)

        # Update the query params
        path = self.orig.view_args.get('path').split('/')

        if len(path) == 1:
            self._scope_security(stripped_args)
            self._patient_security(stripped_args)

        # Determine the URL to proxy to
        url = self._create_url(stripped_args)

        # Strip out headers that might confuse things
        headers = self._strip_disallowed_headers()

        return {
            'headers': headers,
            'method': self.orig.method,
            'url': url,
            'body': self.orig.data,
        }

    def _strip_security_args(self, args):
        return [arg for arg in args if arg[0] != self.SECURITY_ARG_NAME]

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

    def _scope_security(self, args):
        """ Determine which categories the client should be allowed to see
        based on their approved scopes.
        """
        try:
            labels = ','.join(['public'] + self.orig.oauth.access_token.security_labels)
        except AttributeError:
            labels = 'public'

        args.append((self.SECURITY_ARG_NAME, labels))

    def _patient_security(self, args):
        """ Determine which Patients the client should be allowed to see.
        """
        try:
            patient = self.orig.oauth.access_token.patient_id
            labels = 'Patient/{}'.format(patient)
        except AttributeError:
            labels = 'public'

        args.append((self.SECURITY_ARG_NAME, labels))


class UnsecureFlaskClient(FlaskClient):
    """Subclass of FlaskClient, overridden to prevent any security checks """

    # Preserve original security arguments of the request
    def _strip_security_args(self, args):
        return args

    # All the following methods are overridden with a 'pass' to prevent security from being applied to the request.
    def _patient_security(self, args):
        pass

    def _scope_security(self, args):
        pass

    def check_request(self):
        pass
