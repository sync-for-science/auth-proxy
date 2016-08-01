""" Holds the create_app() Flask application factory.
"""
from importlib import import_module
import os

from flask import Flask
import yaml

import auth_proxy as app_root
from auth_proxy.blueprints import all_blueprints
from auth_proxy.extensions import (
    configure,
    csrf,
    db,
    injector,
    login_manager,
    oauth,
)
from auth_proxy.services.login import configure as login_configure
from auth_proxy.services.oauth import configure as oauth_configure
from auth_proxy.services.proxy import configure as proxy_configure


APP_ROOT_FOLDER = os.path.abspath(os.path.dirname(app_root.__file__))
TEMPLATE_FOLDER = os.path.join(APP_ROOT_FOLDER, 'templates')
STATIC_FOLDER = os.path.join(APP_ROOT_FOLDER, 'static')


def get_config(config_class_string, yaml_files=None):
    """ Load the Flask config from a class.

    Args:
        config_class_string (string): a configuration class that will be
            loaded (e.g. 'pypi_portal.config.Production')
        yaml_files (list): YAML files to load. This is for testing, leave
            None in dev/production.

    Returns:
        A class object ot be fed into app.config.from_object().
    """
    config_module, config_class = config_class_string.rsplit('.', 1)
    config_class_object = getattr(import_module(config_module), config_class)
    config_obj = config_class_object()

    # Expand some options
    db_fmt = 'auth_proxy.models.{0}'
    if getattr(config_obj, 'DB_MODELS_IMPORTS', False):
        config_obj.DB_MODELS_IMPORTS = [db_fmt.format(m) for m in config_obj.DB_MODELS_IMPORTS]
    if hasattr(config_obj, 'API_SERVER'):
        config_obj.API_SERVER = os.getenv('API_SERVER', config_obj.API_SERVER)

    # Load additional configuration settings.
    yaml_files = yaml_files or [f for f in [
        os.path.abspath(os.path.join(APP_ROOT_FOLDER, '..', 'config.yml')),
        os.path.join(APP_ROOT_FOLDER, 'config.yml'),
    ] if os.path.exists(f)]
    additional_dict = dict()
    for path in yaml_files:
        with open(path) as handle:
            additional_dict.update(yaml.load(handle.read()))

    return config_obj


def create_app(config_obj, no_sql=False):
    """ Flask application factory. Initializes and returns the Flask
    application.

    Modeled after: http://flask.pocoo.org/docs/patterns/appfactories/

    Args:
        config_obj: configuration object to load into app.config.
        no_sql: does not run init_app() for the SQLAlchemy instance. For Celery compatibility.

    Returns:
        The initialized Flask application.
    """
    # Initialize app. Flatten config_obj to dictionary (resolve properties).
    app = Flask(__name__, template_folder=TEMPLATE_FOLDER, static_folder=STATIC_FOLDER)
    config_dict = dict([(k, getattr(config_obj, k)) for k in dir(config_obj)
                        if not k.startswith('_')])
    app.config.update(config_dict)

    # Import DB models. Flask-SQLAlchemy doesn't do this automatically.
    with app.app_context():
        for module in app.config.get('DB_MODELS_IMPORTS', list()):
            import_module(module)

    # Setup and register views.
    for bpt in all_blueprints:
        import_module(bpt.import_name)
        app.register_blueprint(bpt)

    # Initialize extensions/add-ons/plugins.
    if not no_sql:
        db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    oauth.init_app(app)

    injector.register(configure)
    injector.register(login_configure)
    injector.register(oauth_configure)
    injector.register(proxy_configure)
    injector.init_app(app)

    # Return the application instance.
    return app
