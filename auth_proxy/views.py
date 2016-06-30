# pylint: disable=unused-variable, missing-docstring
""" Views module
"""
from flask import (
    jsonify,
    request,
    render_template,
    url_for,
    Response,
)
from injector import inject

from auth_proxy import services
from auth_proxy import proxy


def configure_views(app, oauth, csrf):

    @app.route('/oauth/register', methods=['POST'])
    @inject(service=services.OAuthService)
    def oauth_register(service):
        client = service.register(
            client_id=request.form['client_id'],
            client_secret=request.form.get('client_secret'),
            redirect_uris=request.form['redirect_uris'],
            scopes=request.form['scopes'],
        )

        return jsonify(client)

    @app.route('/oauth/errors')
    def oauth_errors():
        return jsonify(request.args)

    @app.route('/oauth/token', methods=['GET', 'POST'])
    @oauth.token_handler
    @inject(service=services.OAuthService)
    def cb_oauth_token(service, *args, **kwargs):
        credentials = service.smart_token_credentials(
            grant_type=request.form.get('grant_type'),
            code=request.form.get('code'),
            refresh_token=request.form.get('refresh_token'),
        )

        return credentials

    @app.route('/oauth/authorize', methods=['GET', 'POST'])
    @oauth.authorize_handler
    @inject(service=services.OAuthService)
    def cb_oauth_authorize(service, *args, **kwargs):
        if request.method == 'GET':
            # Additional SMART checks not required by OAuth spec
            assert 'redirect_uri' in request.args, 'Missing redirect_uri.'
            assert 'scope' in request.args, 'Missing scope.'
            assert 'state' in request.args, 'Missing state.'

            client = service.show_authorize_prompt(kwargs['client_id'])
            return render_template('authorize.jinja2',
                                   client=client,
                                   data=kwargs)

        csrf.protect()

        return True

    @app.route('/api/me')
    @inject(service=services.OAuthService)
    @oauth.require_oauth()
    def api_me(service):
        client_id = request.oauth.client.client_id
        tokens = service.audit(client_id)

        return jsonify({
            'client_id': client_id,
            'tokens': [token.interest for token in tokens],
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

    @app.route('/api/fhir/<path:path>', methods=['GET', 'POST'])
    @inject(service=services.ProxyService)
    @oauth.require_oauth()
    def api_fhir_proxy(service, path):
        url = app.config['API_SERVER'] + '/' + path
        response = service.api(url, request)

        return Response(**response)

    @app.route('/api/open-fhir/<path:path>', methods=['GET', 'POST'])
    @inject(service=services.ProxyService)
    def api_open_fhir_proxy(service, path):
        url = app.config['API_SERVER'] + '/' + path
        response = service.api(url, request)

        return Response(**response)

    @app.errorhandler(proxy.ForbiddenError)
    def handle_forbidden_error(error):
        response = jsonify({'error': error.message})
        response.status_code = 401

        return response
