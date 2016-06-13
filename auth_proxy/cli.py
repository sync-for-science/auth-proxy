# pylint: disable=unused-variable, missing-docstring
""" Views module
"""
from flask_sqlalchemy import SQLAlchemy


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
        db.session.add(user.User(id=1, patient_id='smart-1288992'))
        db.session.commit()
