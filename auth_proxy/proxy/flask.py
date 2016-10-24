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
    ccds_scopes = [
        'patient',
        'medications',
        'allergies',
        'immunizations',
        'problems',
        'procedures',
        'vital-signs',
        'laboratory',
        'smoking',
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
            # args.append(('_security', self._patient_security()))

        # Determine the URL to proxy to
        url = self.url + '?' + parse.urlencode(args)

        # Strip out headers that might confuse things
        headers = {key: val for (key, val) in self.orig.headers.items()
                   if key in self.allowed_headers}

        return {
            'headers': headers,
            'method': self.orig.method,
            'url': url,
            'body': self.orig.data,
        }

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
        # Get the authorized scopes from the request, or open everything if
        # this is an un-authorized request
        try:
            scopes = list(self.orig.oauth.scopes)
        except AttributeError:
            scopes = ['patient/*.read']

        # TODO: For some reason, scope is coming through empty, so fill it in
        if not scopes:
            scopes = ['patient/*.read']

        # Wildcard scopes should be expanded
        try:
            wildcard = scopes.index('patient/*.read')
            scopes[wildcard:wildcard] = self.ccds_scopes
        except ValueError:
            pass

        return ','.join(['public'] + scopes)

    def _patient_security(self):
        """ Determine which Patients the client should be allowed to see.

        TODO: Actually do something here
        """
        return ','.join(['public'])
