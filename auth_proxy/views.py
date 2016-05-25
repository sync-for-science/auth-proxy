# pylint: disable=unused-variable, missing-docstring
""" Views module
"""
from flask import jsonify, request, url_for, Response
from injector import inject

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
    @inject(service=services.ProxyService)
    def api_fhir_metadata(service):
        url = app.config['API_SERVER'] + '/metadata'
        authorize = url_for('cb_oauth_authorize', _external=True)
        token = url_for('cb_oauth_token', _external=True)
        register = url_for('oauth_register', _external=True),

        conformance = service.conformance(url=url,
                                          authorize=authorize,
                                          token=token,
                                          register=register)

        return jsonify(conformance)

    @app.route('/api/fhir/<path:path>', methods=['GET'])
    @inject(service=services.ProxyService)
    @oauth.require_oauth()
    def api_fhir_proxy(service, path):
        url = app.config['API_SERVER'] + '/' + path

        response = service.api(url, request)

        return Response(**response)
