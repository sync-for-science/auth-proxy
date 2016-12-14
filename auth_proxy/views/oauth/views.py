# pylint: disable=missing-docstring
""" Views module
"""
import arrow
from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
)
from flask_login import login_required
from furl import furl

from auth_proxy.extensions import csrf, oauthlib
from auth_proxy.services import oauth_service

BP = Blueprint('oauth',
               __name__,
               template_folder='templates',
               url_prefix='/oauth')


@BP.route('/register', methods=['POST'])
def oauth_register():
    client = oauth_service.register(
        client_id=request.form['client_id'],
        client_secret=request.form.get('client_secret'),
        client_name=request.form['client_name'],
        redirect_uris=request.form['redirect_uris'],
        scopes=request.form['scopes'],
    )

    return jsonify(client)


@BP.route('/errors')
def oauth_errors():
    return jsonify(request.args)


@BP.route('/token', methods=['GET', 'POST'])
@oauthlib.token_handler
def cb_oauth_token(*args, **kwargs):
    credentials = oauth_service.smart_token_credentials(
        grant_type=request.form.get('grant_type'),
        code=request.form.get('code'),
        refresh_token=request.form.get('refresh_token'),
    )

    return credentials


@BP.route('/authorize', methods=['GET', 'POST'])
@oauthlib.authorize_handler
@login_required
def cb_oauth_authorize(*args, **kwargs):
    if request.method == 'GET':
        # Additional SMART checks not required by OAuth spec
        assert 'redirect_uri' in request.args, 'Missing redirect_uri.'
        assert 'scope' in request.args, 'Missing scope.'
        assert 'state' in request.args, 'Missing state.'

        client = oauth_service.show_authorize_prompt(kwargs['client_id'])

        abort_uri = furl(kwargs['redirect_uri'])
        abort_uri.args['error'] = 'access_denied'

        today = arrow.utcnow().format('MMMM D, YYYY')
        now = arrow.utcnow().format('h:mma')
        expires = arrow.now().shift(years=1).format('MMMM D, YYYY')

        return render_template('authorize.jinja2',
                               client=client,
                               data=kwargs,
                               today=today,
                               now=now,
                               expires=expires,
                               abort_uri=abort_uri.url)

    csrf.protect()

    return True
