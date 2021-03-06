# pylint: disable=missing-docstring
""" Holds the create_app() Flask application factory.
"""
import os

from flask import Flask


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['WTF_CSRF_CHECK_DEFAULT'] = False

app.config['API_SERVER'] = os.getenv('API_SERVER')
app.config['API_SERVER_NAME'] = os.getenv('API_SERVER_NAME')
app.config['ENABLE_UNSECURE_FHIR'] = os.getenv('ENABLE_UNSECURE_FHIR') == 'True'

app.config['BASE_URL'] = os.getenv('BASE_URL', None)

def create_app():
    from auth_proxy import (
        extensions,
        filters,
    )
    from auth_proxy.views.api.views import BP as api_blueprint
    from auth_proxy.views.cli.views import BP as cli_blueprint
    from auth_proxy.views.main.views import BP as main_blueprint
    from auth_proxy.views.oauth.views import BP as oauth_blueprint

    app.register_blueprint(api_blueprint)
    app.register_blueprint(cli_blueprint)
    app.register_blueprint(main_blueprint)
    app.register_blueprint(oauth_blueprint)

    extensions.db.init_app(app)
    extensions.csrf.init_app(app)
    extensions.login_manager.init_app(app)
    extensions.oauthlib.init_app(app)
    extensions.cors.init_app(app)

    assert filters

    return app
