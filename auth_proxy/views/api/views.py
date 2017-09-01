# pylint: disable=missing-docstring
""" Views module
"""
from flask import (
    Blueprint,
    current_app,
    jsonify,
    request,
    Response,
    url_for,
)

from auth_proxy.extensions import oauthlib
from auth_proxy.proxy import ForbiddenError
from auth_proxy.services import oauth_service, proxy_service

BP = Blueprint('api',
               __name__,
               url_prefix='/api')


@BP.route('/me')
@oauthlib.require_oauth()
def api_me():
    client_id = request.oauth.client.client_id
    tokens = oauth_service.audit(client_id)

    return jsonify({
        'client_id': client_id,
        'tokens': [token.interest for token in tokens],
    })


@BP.route('/fhir/metadata')
def api_fhir_metadata():

    url = current_app.config['API_SERVER'] + '/metadata'
    authorize_url = url_for('oauth.cb_oauth_authorize', _external=True)
    manage_url = url_for('main.apps', _external=True)

    base_url = current_app.config['BASE_URL']
    if base_url:
        authorize_url =  base_url + '/oauth/authorize'
        manage_url =  base_url + '/apps'

    extensions = {
        # The first two URLs need to work from a browser, so we canonicalize
        # them using BASE_URL if available (Flask SERVER_NAME has unexpected
        # consequences making it unsuitable -- see
        # https://github.com/pallets/flask/issues/998)
        'authorize': authorize_url,
        'manage': manage_url,
        'token': url_for('oauth.cb_oauth_token', _external=True),
        'register': url_for('oauth.oauth_register', _external=True),
    }

    conformance = proxy_service.conformance(url, extensions)

    return jsonify(conformance)


@BP.route('/fhir/<path:path>', methods=['GET', 'POST'])
@oauthlib.require_oauth()
def api_fhir_proxy(path):
    url = current_app.config['API_SERVER'] + '/' + path
    response = proxy_service.api(url, request)

    return Response(**response)


@BP.route('/open-fhir/<path:path>', methods=['GET', 'POST'])
def api_open_fhir_proxy(path):
    url = current_app.config['API_SERVER'] + '/' + path
    response = proxy_service.api(url, request)

    return Response(**response)


@BP.errorhandler(ForbiddenError)
def handle_forbidden_error(error):
    response = jsonify({'error': error.message})
    response.status_code = 403

    return response
