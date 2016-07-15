""" Requests specific implementation of Proxy.
"""
import requests

from . import Server

ALLOWED_HEADERS = ['Content-Type', 'Access-Control-Allow-Origin']


class RequestsServer(Server):
    """ Makes a requests request and returns the response.
    """

    def respond(self, request):
        """ @inherit
        """
        response = requests.request(method=request.get('method'),
                                    url=request.get('url'),
                                    headers=request.get('headers'),
                                    data=request.get('body'))

        headers = {key: val for (key, val) in response.headers.items()
                   if key in ALLOWED_HEADERS}

        return {
            'response': response.text,
            'status': response.status_code,
            'headers': headers,
        }
