""" The Proxy module.
"""
from injector import inject


class ForbiddenError(Exception):
    """ Raised when we try and proxy something we shouldn't.
    """
    msg_tmpl = 'Not allowed to query for "{disallowed}" {part}.'

    def __init__(self, segment=None, parameter=None, method=None):
        Exception.__init__(self)
        self.segment = segment
        self.parameter = parameter
        self.method = method

    @property
    def message(self):
        """ Format the message.
        """
        if self.segment is not None:
            return self.msg_tmpl.format(disallowed=self.segment,
                                        part='resource type')
        elif self.parameter is not None:
            return self.msg_tmpl.format(disallowed=self.parameter,
                                        part='parameter')
        elif self.method is not None:
            return self.msg_tmpl.format(disallowed=self.method,
                                        part='method')
        return 'Forbidden'


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

    def check_request(self):
        """ Flags invalid values in the request.

        Raises:
            ForbiddenError: Some things are just too terrible to ignore.
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
        # Make sure it isn't doing anything it shouldn't be
        self.client.check_request()

        # Format the request as a dict we can use.
        request = self.client.request()

        # Format the response as a dict we can use
        response = self.server.respond(request)

        return response
