''' CLI commands.
'''
from flask import Blueprint
import yaml

from auth_proxy.application import app
from auth_proxy.extensions import db


BP = Blueprint('cli', __name__)


@app.cli.command()
def initdb():
    ''' Initialize the database.
    '''
    db.create_all()


@app.cli.command()
def load_fixtures():
    ''' Load fixtures.
    '''
    with open('auth_proxy/fixtures.yml') as handle:
        records = yaml.load_all(handle.read())
        for record in records:
            resource = record['class'](**record['args'])
            db.session.add(resource)
    db.session.commit()
