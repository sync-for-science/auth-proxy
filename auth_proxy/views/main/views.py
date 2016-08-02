# pylint: disable=missing-docstring
""" Views module
"""
from urllib import parse

from flask import (
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required
from injector import inject

from auth_proxy.blueprints import main
from auth_proxy.services.login import LoginService
from auth_proxy.services.oauth import OAuthService


@main.route('/', methods=['GET'])
@login_required
def index():
    return render_template('index.jinja2')


@main.route('/login', methods=['GET', 'POST'])
@inject(service=LoginService)
def login(service):
    if request.method == 'GET':
        # Unquote and re-quote the "next" param because of a bug in werkzeug.
        # https://github.com/pallets/werkzeug/issues/975
        url = request.args.get('next', url_for('.index'))
        parts = list(parse.urlparse(url))
        params = parse.parse_qsl(parts[4])
        parts[4] = parse.urlencode(params)
        url = parse.urlunparse(parts)

        return render_template('login.jinja2', next=url)

    try:
        service.log_in_user(request.form['username'],
                            request.form['password'])
        redirect_to = request.form.get('next')

        if redirect_to and redirect_to.startswith('/'):
            return redirect(redirect_to)

        return redirect(url_for('.index'))
    except Exception as err:  # pylint: disable=broad-except
        return render_template('login.jinja2',
                               error=err,
                               next=redirect_to)


@main.route('/logout')
@inject(service=LoginService)
def logout(service):
    service.log_out_user()

    return redirect(url_for('.login'))


@main.route('/apps')
@login_required
@inject(service=OAuthService)
def apps(service):
    tokens = service.authorizations()

    return render_template('apps.jinja2', authorizations=tokens)


@main.route('/revoke/<int:token_id>', methods=['POST'])
@login_required
@inject(service=OAuthService)
def revoke(service, token_id):
    service.revoke_token(token_id)

    return redirect(url_for('.apps'))
