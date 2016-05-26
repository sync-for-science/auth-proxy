""" Flask specific implementation of Proxy.
"""
from urllib import parse

from . import Client, ForbiddenError


class FlaskClient(Client):
    """ Converts a Flask request object into a generic one.
    """
    allowed_headers = ['Accept']
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
        'AllergyIntolerance',
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
        args = dict(self.orig.args)

        # Get the authorized scopes from the request, or open everything if
        # this is an un-authorized request
        try:
            scopes = list(self.orig.oauth.scopes)
        except AttributeError:
            scopes = ['patient/*.read',]

        # Wildcard scopes should be expanded
        try:
            wildcard = scopes.index('patient/*.read')
            scopes[wildcard:wildcard] = self.ccds_scopes
        except ValueError:
            pass

        # Update the query params
        args['_security'] = ' '.join(scopes + ['public'] + args.get('_security', ''))

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
