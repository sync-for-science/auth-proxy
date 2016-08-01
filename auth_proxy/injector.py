""" FlaskInjector module.
"""
from flask_injector import FlaskInjector
from injector import Injector


class InjectorExtension(object):
    """ Wrapper for FlaskInjector so it can be lazy loaded.
    """
    def __init__(self):
        self.injector = None
        self.modules = []

    def register(self, module):
        """ Add a module to be registered later.
        """
        self.modules.append(module)

    def init_app(self, app):
        """ Init the Flask app.
        """
        self.injector = Injector(self.modules)
        FlaskInjector(app=app, injector=self.injector)
