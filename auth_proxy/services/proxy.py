""" Services module.
"""
import requests

from auth_proxy.proxy import Proxy
from auth_proxy.proxy.flask import FlaskClient
from auth_proxy.proxy.requests import RequestsServer


class ProxyService(object):
    """ Handle proxying the FHIR API.
    """
    def conformance(self, url, authorize=None, token=None, register=None):
        """ Proxy the conformance statement.
        We need to set the oAuth uris extension though.
        """
        headers = {
            'Accept': 'application/json+fhir',
        }
        response = requests.get(url, headers=headers)
        conformance = response.json()

        extension = {
            'url': 'http://fhir-registry.smarthealthit.org/StructureDefinition/oauth-uris',
            'extension': [],
        }

        if authorize is not None:
            extension['extension'].append({
                'url': 'authorize',
                'valueUri': authorize,
            })

        if token is not None:
            extension['extension'].append({
                'url': 'token',
                'valueUri': token,
            })

        if register is not None:
            extension['extension'].append({
                'url': 'register',
                'valueUri': register,
            })

        security = conformance['rest'][0].get('security', {})
        security['extension'] = [extension]
        conformance['rest'][0]['security'] = security

        return conformance

    def api(self, url, request):
        """ Proxy FHIR API requests.
        """
        client = FlaskClient(url, request)
        server = RequestsServer()
        proxy = Proxy(client, server)

        return proxy.proxy()


def configure(binder):
    """ Configure this module for the Injector.
    """
    binder.bind(ProxyService)
