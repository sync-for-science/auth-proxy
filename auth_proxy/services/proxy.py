""" Services module.
"""
import requests

from auth_proxy.proxy import Proxy
from auth_proxy.proxy.flask import FlaskClient
from auth_proxy.proxy.requests import RequestsServer


class ProxyService(object):
    """ Handle proxying the FHIR API."""
    def __init__(self):
        self.default_client_factory = FlaskClient

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

        service = {
            'coding': [{
                'system': 'http://hl7.org/fhir/restful-security-service',
                'code': 'SMART-on-FHIR'
            }],
            'text': 'OAuth2 using SMART-on-FHIR profile (see http://docs.smarthealthit.org)'
        }

        security = conformance['rest'][0].get('security', {})
        security['extension'] = [extension]
        security['service'] = [service]
        conformance['rest'][0]['security'] = security

        return conformance

    def api(self, url, request, client_factory=None):
        """ Proxy FHIR API requests.
        """
        client_factory = client_factory or self.default_client_factory
        client = client_factory(url, request)
        server = RequestsServer()
        proxy = Proxy(client, server)

        return proxy.proxy()


def configure(binder):
    """ Configure this module for the Injector.
    """
    binder.bind(ProxyService)
