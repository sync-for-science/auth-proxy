""" Services module.
"""
import requests

from auth_proxy.proxy import Proxy
from auth_proxy.proxy.flask import FlaskClient
from auth_proxy.proxy.requests import RequestsServer


class ProxyService(object):
    """ Handle proxying the FHIR API.
    """
    def conformance(self, url, extensions=None):
        """ Proxy the conformance statement.
        We need to set the oAuth uris extension though.
        """
        if not extensions:
            extensions = []

        headers = {
            'Accept': 'application/json+fhir',
        }
        response = requests.get(url, headers=headers)
        conformance = response.json()

        extension = {
            'url': 'http://fhir-registry.smarthealthit.org/StructureDefinition/oauth-uris',
            'extension': [],
        }

        for url, valueUri in extensions.items():
            extension['extension'].append({
                'url': url,
                'valueUri': valueUri,
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
