""" Flask specific implementation of Proxy.
"""
from urllib.parse import urlencode

from . import Client


class FlaskClient(Client):
    """ Converts a Flask request object into a generic one.
    """
    def __init__(self, url, orig):
        self.url = url
        self.orig = orig

    def request(self):
        """ @inherit
        """
        url = self.url + '?' + urlencode(self.orig.args)
        headers = {key: val for (key, val) in self.orig.headers.items()
                   if key in ['Accept']}

        return {
            'headers': headers,
            'method': self.orig.method,
            'url': url,
            'body': self.orig.data,
        }
