# pylint: disable=missing-docstring
""" Views module
"""
from urllib import parse

from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required

from auth_proxy.services import login_service, oauth_service

BP = Blueprint('main',
               __name__,
               template_folder='templates')


@BP.route('/', methods=['GET'])
@login_required
def index():
    return render_template('index.jinja2')


@BP.route('/login')
def login():
    # Unquote and re-quote the "next" param because of a bug in werkzeug.
    # https://github.com/pallets/werkzeug/issues/975
    url = request.args.get('next', url_for('.index'))
    parts = list(parse.urlparse(url))
    params = parse.parse_qsl(parts[4])
    parts[4] = parse.urlencode(params)
    url = parse.urlunparse(parts)

    return render_template('login.jinja2', next=url)


@BP.route('/login', methods=['POST'])
def handle_login():
    redirect_to = request.form.get('next')

    try:
        login_service.log_in_user(request.form['username'],
                                  request.form['password'])

        if redirect_to and redirect_to.startswith('/'):
            return redirect(redirect_to)

        return redirect(url_for('.index'))
    except Exception as err:  # pylint: disable=broad-except
        return render_template('login.jinja2',
                               error=err,
                               next=redirect_to)


@BP.route('/logout')
def logout():
    login_service.log_out_user()

    return redirect(url_for('.login'))


@BP.route('/apps')
@login_required
def apps():
    tokens = oauth_service.authorizations()

    return render_template('apps.jinja2', authorizations=tokens)


@BP.route('/revoke/<int:token_id>', methods=['POST'])
@login_required
def revoke(token_id):
    oauth_service.revoke_token(token_id)

    return redirect(url_for('.apps'))
