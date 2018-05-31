# pylint: disable=missing-docstring
""" Views module
"""
import time

import arrow
from flask import (
    Blueprint,
    jsonify,
    render_template,
    request
)
from flask_login import current_user, login_required
from furl import furl

from auth_proxy.extensions import csrf, oauthlib
from auth_proxy.services import oauth_service
from auth_proxy.models.oauth import Token
from auth_proxy.services import OAuthServiceError


BP = Blueprint('oauth',
               __name__,
               template_folder='templates',
               url_prefix='/oauth')


@BP.route('/register', methods=['POST'])
def oauth_register():
    if not request.json:
        raise OAuthServiceError(
            'bad_request',
            'The request requires a JSON payload.'
        )

    client = oauth_service.register(
        client_name=request.json.get('client_name'),
        redirect_uris=request.json.get('redirect_uris'),
        scopes=request.json.get('scope', ''),
    )

    response = jsonify(client)
    response.status_code = 201  # created

    return response


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


@BP.route('/debug/token', methods=['POST'])
def debug_create_token(*args, **kwargs):

    token_json = request.get_json()

    default_access_lifetime = 60*60  # 1 hour
    default_approval_expiry = time.time() + 365*24*60*60  # 1 year from now

    token = oauth_service.create_debug_token(
        client_id=token_json.get('client_id'),
        access_lifetime=token_json.get('access_lifetime', default_access_lifetime),
        approval_expires=token_json.get('approval_expires', default_approval_expiry),
        scopes=token_json.get('scope'),
        user=token_json.get('username'),
        patient_id=token_json.get('patient_id')
    )

    return jsonify({'access_token': token.access_token, 'refresh_token': token.refresh_token})


@BP.route('/debug/introspect/<token>', methods=['GET'])
def debug_token_introspection(token, *args, **kwargs):

    passed_token = Token.query.filter_by(access_token=token).first()

    if not passed_token:
        passed_token = Token.query.filter_by(refresh_token=token).first()

    if not passed_token:
        raise OAuthServiceError('no_token', 'No matching token found.')

    return jsonify(passed_token.interest)


@BP.route('/authorize', methods=['GET', 'POST'])
@oauthlib.authorize_handler
@login_required
def cb_oauth_authorize(*args, **kwargs):
    if request.method == 'POST':
        csrf.protect()

        oauth_service.create_authorization(
            client_id=request.form['client_id'],
            expires=request.form['expires'],
            security_labels=request.form['security_labels'],
            user=current_user,
            patient_id=request.form['patient_id'],
        )

        return True

    # Additional SMART checks not required by OAuth spec
    assert 'redirect_uri' in request.args, 'Missing redirect_uri.'
    assert 'scope' in request.args, 'Missing scope.'
    assert 'state' in request.args, 'Missing state.'

    # Get the patient_id from GET query or use a default patient id
    patient_id = request.args.get('patient_id',
                                  current_user.default_patient_id)

    # If we still don't have a patient id, show the delegation prompt
    if not patient_id:
        return render_template('delegate.jinja2')

    # Make sure that this User can approve on behalf of this Patient
    patient = current_user.patient(patient_id)
    assert patient, 'Invalid patient id.'

    client = oauth_service.show_authorize_prompt(kwargs['client_id'])

    abort_uri = furl(kwargs['redirect_uri'])
    abort_uri.args['error'] = 'access_denied'

    today = arrow.utcnow().isoformat()
    expires = arrow.utcnow().shift(years=1).format('YYYY-MM-DD')

    # Show a different template for delegation workflow
    if patient.is_user:
        template = 'authorize_self.jinja2'
    else:
        template = 'authorize_other.jinja2'

    return render_template(template,
                           patient=patient,
                           client=client,
                           data=kwargs,
                           today=today,
                           expires=expires,
                           abort_uri=abort_uri.url)

@BP.errorhandler(OAuthServiceError)
def handle_oauth_error(error):
    response = jsonify(error=error.error, description=error.description)
    response.status_code = 400

    return response
