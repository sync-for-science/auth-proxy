# pylint: disable=missing-docstring
""" Views module
"""
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
from auth_proxy.models.user import User

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


@BP.route('/debug/token', methods=['POST'])
def debug_create_token(*args, **kwargs):

    token_json = request.get_json()

    creating_user = User.query.filter_by(username=token_json["user"]).first()

    token = oauth_service.create_token(
        client_id=token_json["client_id"],
        expires=token_json["expires"],
        security_labels=token_json["security_labels"],
        user=creating_user,
        patient_id=token_json["patient_id"]
    )

    refreshed_token = token.refresh("access1234", "refresh1234", token_json["expires"], "Bearer", token_json["security_labels"])

    return jsonify({"access_token": refreshed_token.access_token})


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
