""" Login Service module.
"""
import flask_login
from flask_sqlalchemy import SQLAlchemy
from injector import inject, singleton

from auth_proxy.models.user import User


class LoginService(object):
    """ Handle all our login operations.
    """
    @inject(db=SQLAlchemy, login_manager=flask_login.LoginManager)
    def __init__(self, db, login_manager):
        self.db = db
        self.login_manager = login_manager

        login_manager.login_view = 'main.views.login'
        login_manager.user_loader(self.load_user)

    def load_user(self, user_id):
        """ LoginManager user_loader callback.
        """
        user = self.db.session.query(User).\
            filter_by(id=user_id).first()

        return user

    def log_in_user(self, username, password):
        """ Handle the login process.
        """
        user = self.db.session.query(User).\
            filter_by(username=username).first()

        assert user, 'User not found.'
        assert user.password == password, 'Incorrect password.'

        flask_login.login_user(user)

    def log_out_user(self):
        """ Handle the logout process.
        """
        flask_login.logout_user()


def configure(binder):
    """ Configure this module for the Injector.
    """
    binder.bind(LoginService, scope=singleton)
    binder.injector.get(LoginService)
