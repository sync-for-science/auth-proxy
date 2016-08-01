# pylint: disable=missing-docstring
""" Views module
"""
from flask import (
    jsonify,
    render_template,
    request,
)
from flask_login import login_required
from flask_wtf.csrf import CsrfProtect
from furl import furl
from injector import inject

from auth_proxy.blueprints import oauth
from auth_proxy.extensions import oauth as oauthlib
from auth_proxy.services.oauth import OAuthService


@oauth.route('/register', methods=['POST'])
@inject(service=OAuthService)
def oauth_register(service):
    client = service.register(
        client_id=request.form['client_id'],
        client_secret=request.form.get('client_secret'),
        redirect_uris=request.form['redirect_uris'],
        scopes=request.form['scopes'],
    )

    return jsonify(client)


@oauth.route('/errors')
def oauth_errors():
    return jsonify(request.args)


@oauth.route('/token', methods=['GET', 'POST'])
@oauthlib.token_handler
@inject(service=OAuthService)
def cb_oauth_token(service, *args, **kwargs):
    credentials = service.smart_token_credentials(
        grant_type=request.form.get('grant_type'),
        code=request.form.get('code'),
        refresh_token=request.form.get('refresh_token'),
    )

    return credentials


@oauth.route('/authorize', methods=['GET', 'POST'])
@oauthlib.authorize_handler
@login_required
@inject(service=OAuthService, csrf=CsrfProtect)
def cb_oauth_authorize(service, csrf, *args, **kwargs):
    if request.method == 'GET':
        # Additional SMART checks not required by OAuth spec
        assert 'redirect_uri' in request.args, 'Missing redirect_uri.'
        assert 'scope' in request.args, 'Missing scope.'
        assert 'state' in request.args, 'Missing state.'

        client = service.show_authorize_prompt(kwargs['client_id'])

        abort_uri = furl(kwargs['redirect_uri'])
        abort_uri.args['error'] = 'access_denied'

        return render_template('authorize.jinja2',
                               client=client,
                               data=kwargs,
                               abort_uri=abort_uri.url)

    csrf.protect()

    return True
