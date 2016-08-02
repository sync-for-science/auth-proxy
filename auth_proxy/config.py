# pylint: disable=missing-docstring
class Config(object):
    """ Default Flask configuration inherited by all environments.
    Use this for development environments.
    """
    DEBUG = True
    TESTING = True
    SECRET_KEY = 'secret'

    DB_MODELS_IMPORTS = ()
    SQLALCHEMY_DATABASE_URI = 'sqlite:///db.sqlite'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    API_SERVER = None
    WTF_CSRF_CHECK_DEFAULT = False


class Testing(Config):
    TESTING = True


class Production(Config):
    DEBUG = False
