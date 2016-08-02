# pylint: disable=missing-docstring
""" Views module
"""
from flask import (
    current_app,
    jsonify,
    request,
    Response,
    url_for,
)
from injector import inject

from auth_proxy.blueprints import api
from auth_proxy.extensions import oauth as oauthlib
from auth_proxy.proxy import ForbiddenError
from auth_proxy.services import oauth, proxy


@api.route('/me')
@inject(service=oauth.OAuthService)
@oauthlib.require_oauth()
def api_me(service):
    client_id = request.oauth.client.client_id
    tokens = service.audit(client_id)

    return jsonify({
        'client_id': client_id,
        'tokens': [token.interest for token in tokens],
    })


@api.route('/fhir/metadata')
@inject(service=proxy.ProxyService)
def api_fhir_metadata(service):
    url = current_app.config['API_SERVER'] + '/metadata'
    authorize = url_for('oauth.views.cb_oauth_authorize', _external=True)
    token = url_for('oauth.views.cb_oauth_token', _external=True)
    register = url_for('oauth.views.oauth_register', _external=True)

    conformance = service.conformance(url=url,
                                      authorize=authorize,
                                      token=token,
                                      register=register)

    return jsonify(conformance)


@api.route('/fhir/<path:path>', methods=['GET', 'POST'])
@inject(service=proxy.ProxyService)
@oauthlib.require_oauth()
def api_fhir_proxy(service, path):
    url = current_app.config['API_SERVER'] + '/' + path
    response = service.api(url, request)

    return Response(**response)


@api.route('/open-fhir/<path:path>', methods=['GET', 'POST'])
@inject(service=proxy.ProxyService)
def api_open_fhir_proxy(service, path):
    url = current_app.config['API_SERVER'] + '/' + path
    response = service.api(url, request)

    return Response(**response)


@api.errorhandler(ForbiddenError)
def handle_forbidden_error(error):
    response = jsonify({'error': error.message})
    response.status_code = 401

    return response
