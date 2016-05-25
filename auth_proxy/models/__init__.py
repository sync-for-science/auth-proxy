""" Models module
"""
from sqlalchemy.ext.declarative import declarative_base


# We use standard SQLAlchemy models rather than the Flask-SQLAlchemy magic, as
# it requires a global Flask app object and SQLAlchemy db object.
Base = declarative_base()
