# pylint: disable=unused-variable, missing-docstring
""" Views module
"""
from flask_sqlalchemy import SQLAlchemy
import yaml


def configure_views(app, injector):
    """ Configure cli scripts.

    NB: passing injector into this method is unfortunate, because it breaks
    inverstion of control, but FlaskInjector isn't set up to work properly
    with cli commands yet.
    """
    @app.cli.command()
    def initdb():
        from auth_proxy.models import Base, oauth, user

        db = injector.get(SQLAlchemy)

        Base.metadata.create_all(db.engine)
        with open('auth_proxy/fixtures.yml') as handle:
            records = yaml.load_all(handle.read())
            for record in records:
                resource = record['class'](**record['args'])
                db.session.add(resource)
        db.session.commit()
