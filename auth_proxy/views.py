# pylint: disable=unused-variable, missing-docstring
""" Views module
"""
import os

from flask import jsonify, request, url_for, Response
from injector import inject
import requests

from auth_proxy import services


def configure_views(app, oauth):

    @app.route('/oauth/register', methods=['POST'])
    @inject(service=services.OAuthService)
    def oauth_register(service):
        client = service.register(
            client_id=request.form['client_id'],
            redirect_uris=request.form['redirect_uris'],
            scopes=request.form['scopes'],
        )

        return jsonify(client)

    @app.route('/oauth/errors')
    def oauth_errors():
        return jsonify(request.args)

    @app.route('/oauth/token', methods=['GET', 'POST'])
    @oauth.token_handler
    def cb_oauth_token(*args, **kwargs):
        return None

    @app.route('/oauth/authorize', methods=['GET', 'POST'])
    @oauth.authorize_handler
    def cb_oauth_authorize(*args, **kwargs):
        return True

    @app.route('/api/me')
    @oauth.require_oauth()
    def api_me():
        return jsonify({
            'client_id': request.oauth.client.client_id,
        })

    @app.route('/api/fhir/metadata')
    def api_fhir_metadata():
        url = os.getenv('API_SERVER') + '/metadata'
        headers = {
            'Accept': 'application/json+fhir',
        }
        response = requests.get(url, headers=headers)
        conformance = response.json()

        security = conformance['rest'][0].get('security', {})

        security['extension'] = [{
            'url': 'http://fhir-registry.smarthealthit.org/StructureDefinition/oauth-uris',
            'extension': [{
                'url': 'authorize',
                'valueUri': url_for('cb_oauth_authorize', _external=True),
            }, {
                'url': 'token',
                'valueUri': url_for('cb_oauth_token', _external=True),
            }, {
                'url': 'register',
                'valueUri': url_for('oauth_register', _external=True),
            }]
        }]
        conformance['rest'][0]['security'] = security

        return jsonify(conformance)

    @app.route('/api/fhir/<path:path>')
    @oauth.require_oauth()
    def api_fhir_proxy(path):
        url = os.getenv('API_SERVER') + '/' + path

        headers = {key: val for (key, val) in request.headers.items()
                   if key in ['Accept']}

        response = requests.get(url,
                                headers=headers,
                                params=request.args)

        headers = {key: val for (key, val) in response.headers.items()
                   if key in ['Content-Type']}

        return Response(response=response.text,
                        headers=headers,
                        status=response.status_code)
