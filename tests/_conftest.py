# _conftest.py -- provides the actual configuration file for the tests that gets
# loaded in `test_plugin.py`
import os

import pytest
import sqlalchemy as sa
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from pytest_postgresql.janitor import DatabaseJanitor

# Retrieve a database connection string from the shell environment
try:
    DB_CONN = os.environ['TEST_DATABASE_URL']
except KeyError:
    raise KeyError('TEST_DATABASE_URL not found. You must export a database ' +
                   'connection string to the environmental variable ' +
                   'TEST_DATABASE_URL in order to run tests.')
else:
    DB_OPTS = sa.engine.url.make_url(DB_CONN).translate_connect_args()

pytest_plugins = ['pytest-flask-sqlalchemy']


@pytest.fixture(scope='session')
def database(request):
    '''
    Create a Postgres database for the tests, and drop it when the tests are done.
    '''
    pg_host = DB_OPTS.get("host")
    pg_port = DB_OPTS.get("port")
    pg_user = DB_OPTS.get("username")
    pg_pass = DB_OPTS.get("password")
    pg_db = DB_OPTS["database"]

    janitor = DatabaseJanitor(
        user=pg_user,
        host=pg_host,
        port=pg_port,
        db_name=pg_db,
        version='9.6',
        password=pg_pass
    )
    janitor.init()

    @request.addfinalizer
    def drop_database():
        janitor.drop()


@pytest.fixture(scope='session')
def app(database):
    '''
    Create a Flask app context for the tests.
    '''
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = DB_CONN

    return app


@pytest.fixture(scope='session')
def _db(app):
    '''
    Provide the transactional fixtures with access to the database via a Flask-SQLAlchemy
    database connection.
    '''
    db = SQLAlchemy(app=app)
    return db


@pytest.fixture(scope='module')
def person(request, _db):
    '''
    Create a table to use for updating in the process of testing direct database access.
    '''
    class Person(_db.Model):
        __tablename__ = 'person'
        id = _db.Column(_db.Integer, primary_key=True)
        name = _db.Column(_db.String(80))

    # Create tables
    _db.create_all()

    @request.addfinalizer
    def drop_tables():
        _db.drop_all()

    return Person


@pytest.fixture(scope='module')
def account_address(request, _db, person):
    '''
    Create tables to use for testing deletes and relationships.
    '''
    class Account(_db.Model):
        __tablename__ = 'account'

        id = _db.Column(_db.Integer, primary_key=True)
        addresses = _db.relationship(
            'Address',
            back_populates='account',
        )

    class Address(_db.Model):
        __tablename__ = 'address'

        id = _db.Column(_db.Integer, primary_key=True)

        account_id = _db.Column(_db.Integer, _db.ForeignKey('account.id'))
        account = _db.relationship('Account', back_populates='addresses')

    # Create tables
    _db.create_all()

    @request.addfinalizer
    def drop_tables():
        _db.drop_all()

    return Account, Address
