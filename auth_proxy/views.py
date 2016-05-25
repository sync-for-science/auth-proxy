# pylint: disable=unused-variable, missing-docstring
""" Views module
"""
from flask import jsonify, request, url_for
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
    def api_fhir_metadata():
        return jsonify({
            'token': url_for('cb_oauth_token', _external=True),
            'authorize': url_for('cb_oauth_authorize', _external=True),
            'register': url_for('oauth_register', _external=True),
        })
