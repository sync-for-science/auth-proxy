""" The Proxy module.
"""
from injector import inject


class Client(object):
    """ A Proxy Client interface.
    """
    def request(self):
        """ Transforms a framework request into a generic one.

        Returns:
            A dict describing the request. Contains:
                - url
                - headers
                - method
                - body
        """
        raise NotImplementedError


class Server(object):
    """ A Proxy Server interface.
    """
    def respond(self, request):
        """ Makes the provided request and returns the response.

        Returns:
            A dict describing the response. Contains:
                - response
                - status
                - headers
        """
        raise NotImplementedError


class Proxy(object):
    """ The proxy skeleton.
    """
    def __init__(self, client, server):
        self.client = client
        self.server = server

    def proxy(self):
        """ Proxies the request and returns the response.
        """
        request = self.client.request()
        response = self.server.respond(request)

        return response
