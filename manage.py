#!/usr/bin/env python
""" Main entry point into the "AuthProxy" Flask application.

Command details:
    devserver                       Run the application using the Flask
                                    Development Server. Auto-reloads files
                                    when they change.
    wsgi_app                        Return the application so that an external
                                    server can handle the details.
    initialize_db                   Initialize database tables, create a
                                    Participant record.

Usage:
    manage.py devserver [-p NUM] [-l DIR] [--config_prod]
    manage.py wsgi_app [-l DIR] [--config_prod]
    manage.py initialize_db

Options:
    --config_prod               Load the production configuration instead of
                                development.
    -l DIR --log_dir=DIR        Log all statements to file in this directory
                                instead of stdout.
                                Only ERROR statements will go to stdout. stderr
                                is not used.
    -p NUM --port=NUM           Flask will listen on this port number.
                                [default: 5000]
"""
from functools import wraps
import logging
import os
import signal
import sys

from docopt import docopt

from auth_proxy.application import create_app, get_config
from auth_proxy.extensions import injector

OPTIONS = docopt(__doc__)


class CustomFormatter(logging.Formatter):  # pylint: disable=missing-docstring
    LEVEL_MAP = {
        logging.FATAL: 'F',
        logging.ERROR: 'E',
        logging.WARN: 'W',
        logging.INFO: 'I',
        logging.DEBUG: 'D'
    }

    def format(self, record):
        record.levelletter = self.LEVEL_MAP[record.levelno]
        return super(CustomFormatter, self).format(record)


def setup_logging(name=None):
    """ Setup Google-Style logging for the entire application.

    At first I hated this but I had to use it for work, and now I prefer it. Who knew?
    From:
        https://github.com/twitter/commons/blob/master/src/python/twitter/common/log/formatters/glog.py

    Always logs DEBUG statements somewhere.

    Positional arguments:
        name -- Append this string to the log file filename.
    """
    log_to_disk = False
    if OPTIONS['--log_dir']:
        if not os.path.isdir(OPTIONS['--log_dir']):
            print('ERROR: Directory {} does not exist.'.format(OPTIONS['--log_dir']))
            sys.exit(1)
        if not os.access(OPTIONS['--log_dir'], os.W_OK):
            print('ERROR: No permissions to write to directory {}.'.format(OPTIONS['--log_dir']))
            sys.exit(1)
        log_to_disk = True

    fmt = '%(levelletter)s%(asctime)s.%(msecs).03d %(process)d %(filename)s:%(lineno)d] %(message)s'
    datefmt = '%m%d %H:%M:%S'
    formatter = CustomFormatter(fmt, datefmt)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.ERROR if log_to_disk else logging.DEBUG)
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(console_handler)

    if log_to_disk:
        file_name = os.path.join(OPTIONS['--log_dir'], 'pypi_portal_{}.log'.format(name))
        file_handler = logging.handlers.TimedRotatingFileHandler(file_name, when='d', backupCount=7)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)


def parse_options():
    """ Parses command line options for Flask.

    Returns:
        Config instance to pass into create_app().
    """
    # Figure out which class will be imported.
    if OPTIONS['--config_prod']:
        config_class_string = 'auth_proxy.config.Production'
    else:
        config_class_string = 'auth_proxy.config.Config'
    config_obj = get_config(config_class_string)

    return config_obj


def command(func):
    """ Decorator that register the chosen command/function.

    If a function is decorated with @command but that function name is not
    a valid "command" according to the docstring, a KeyError will be raised,
    since that's a bug in this script.

    If a user doesn't specify a valid command in their command line
    arguments, the above docopt(__doc__) line will print a short summary and
    call sys.exit() and stop up there.

    If a user specifies a valid command, but for some reason the deveoper
    did not register it, an AttributeError will be raise, since it is a bug
    in this script.

    Finally, if a user specifies a valid command and it is registered with
    @command below, then that command is "chosen" by this decorator function,
    and set as the attribute `chosen`. It is then executed below in
    `if __name__ == '__main__':`.

    Doing this instead of using Flask-Script.

    Positional arguments:
        func -- the function to decorate
    """
    @wraps(func)
    def wrapped():  # pylint: disable=missing-docstring
        return func()

    # Register chosen function.
    if func.__name__ not in OPTIONS:
        message = 'Cannot register {0}, not mentioned in docstring/docopt.'.format(func.__name__)
        raise KeyError(message)
    if OPTIONS[func.__name__]:
        command.chosen = func

    return wrapped


@command
def devserver():  # pylint: disable=missing-docstring
    setup_logging('devserver')
    app = create_app(parse_options())
    app.run(host='0.0.0.0', port=int(OPTIONS['--port']))


@command
def wsgi_app():  # pylint: disable=missing-docstring
    setup_logging('wsgi_app')
    app = create_app(parse_options())
    return app


@command
def initialize_db():
    """ Initialize database tables, create a Participant record.
    """
    from auth_proxy.extensions import db
    import yaml

    setup_logging('shell')
    app = create_app(parse_options())
    app.app_context().push()

    db.create_all()

    with open('auth_proxy/fixtures.yml') as handle:
        records = yaml.load_all(handle.read())
        for record in records:
            resource = record['class'](**record['args'])
            db.session.add(resource)
    db.session.commit()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))  # Properly handle Control+C
    if not OPTIONS['--port'].isdigit():
        print('ERROR: Port should be a number.')
        sys.exit(1)
    getattr(command, 'chosen')()  # Execute the function specified by the user.