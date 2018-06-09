# pytest-flask-sqlalchemy-transactions

[![Build Status](https://travis-ci.org/jeancochrane/pytest-flask-sqlalchemy-transactions.svg?branch=master)](https://travis-ci.org/jeancochrane/pytest-flask-sqlalchemy-transactions) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/Django.svg)

A [pytest](https://docs.pytest.org/en/latest/) plugin providing fixtures for running tests in
transactions using [Flask-SQLAlchemy](http://flask-sqlalchemy.pocoo.org/latest/).

## Contents

- [**Motivation**](#motivation)
- [**Quick examples**](#quick-examples)
- [**Usage**](#usage)
    - [Installation](#installation)
        - [From PyPi](#from-pypi)
        - [Development version](#development-version)
    - [Configuration](#configuration)
        - [Conftest setup](#conftest-setup)
        - [Test configuration](#test-configuration)
            - [`mocked-engines`](#mocked-engines)
            - [`mocked-sessions`](#mocked-sessions)
            - [`mocked-sessionmakers`](#mocked-sessionmakers)
    - [Fixtures](#fixtures)
        - [`db_session`](#db_session)
        - [`db_engine`](#db_engine)
    - [Using the `transactional` mark](#using-the-transactional-mark)
- [**Development**](#development)
    - [Running the tests](#running-the-tests)
    - [Acknowledgements](#acknowledgements)
    - [Copyright](#copyright)

## Motivation

Inspired by [Django's built-in support for transactional
tests](https://jeancochrane.com/blog/django-test-transactions), this plugin 
seeks to provide comprehensive, easy-to-use Pytest fixtures for wrapping tests in
database transactions for [Flask-SQLAlchemy](http://flask-sqlalchemy.pocoo.org/latest/)
apps. The goal is to make testing stateful Flask-SQLAlchemy applications easier by
providing fixtures that permit the developer to **make arbitrary database updates
with the confidence that any changes made during a test will roll back** once the test exits.

## Quick examples

Use the [`db_session` fixture](#db_session) to make **database updates that won't persist beyond
the body of the test**:

```python
def test_a_transaction(db_session):
   row = db_session.query(Table).get(1) 
   row.name = 'testing'

   db_session.add(row)
   db_session.commit()

def test_transaction_doesnt_persist(db_session):
   row = db_session.query(Table).get(1) 
   assert row.name != 'testing'
```

The [`db_engine` fixture](#db_engine) works the same way, but **copies the API of
SQLAlchemy's [Engine
object](http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine)**:

```python
def test_a_transaction_using_engine(db_engine):
    with db_engine.begin() as conn:
        row = conn.execute('''UPDATE table SET name = 'testing' WHERE id = 1''')

def test_transaction_doesnt_persist(db_engine):
    row_name = db_engine.execute('''SELECT name FROM table WHERE id = 1''').fetchone()[0]
    assert row_name != 'testing' 
```

Use [configuration properties](#test-configuration) to
**mock database connections in an app and enforce nested transactions**,
allowing any method from the codebase to run inside a test with the assurance
that any database changes made will be rolled back at the end of the test:

```ini
# tests/tox.ini

[pytest]
mocked-sessions=api.database.db.session
mocked-engines=api.database.engine
```

```python
# api/database.py

db = flask_sqlalchemy.SQLAlchemy()
engine = sqlalchemy.create_engine('db_connection_string')
```

```python
# api/models.py

class Table(db.Model):
    __tablename__ = 'table'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))

    def set_name(new_name)
        self.name = new_name
        db.session.add(self)
        db.session.commit()
```

```python
# tests/test_api.py

def test_set_name(db_session):
    row = db_session.query(Table).get(1)
    row.set_name('testing')
    assert row.name == 'testing'

def test_transaction_doesnt_persist(db_session):
   row = db_session.query(Table).get(1) 
   assert row.name != 'testing'
```

Use the [`@pytest.mark.transactional` mark](#using-the-transactional-mark) 
to **enforce that a test gets run inside a transaction**:

```python
from api.database import db

@pytest.mark.transactional
def test_db_update():
    row = db.session.query(Table).get(1)
    row.name = 'testing'
    db.session.add(row)
    db.session.commit()

@pytest.mark.transactional
def test_db_update_doesnt_persist():
    row = db.session.query(Table).get(1)
    assert row.name != 'testing'
```

# Usage

## Installation

### From PyPi

Install using pip:

```
pip install pytest-flask-sqlalchemy-transactions
```

Once installed, pytest will detect the plugin automatically during test collection.
For basic background on using third-party plugins with pytest, see the [pytest
documentation](https://docs.pytest.org/en/latest/plugins.html?highlight=plugins).

### Development version

Clone the repo from GitHub and switch into the new directory:

```
git clone git@github.com:jeancochrane/pytest-flask-sqlalchemy-transactions.git
cd pytest-flask-sqlalchemy-transactions
```

You can install using pip:

```
pip install .
```

Or install the plugin dependencies manually:

```
pip install -r requirements/main.txt
```

## Configuration

### Conftest setup

This plugin assumes that a fixture called `_db` has been
defined in the root conftest file for your tests. The `_db` fixture should
expose access to a valid [SQLAlchemy `Session` object](http://docs.sqlalchemy.org/en/latest/orm/session_api.html?highlight=session#sqlalchemy.orm.session.Session) that can interact with your database,
for example via the [`SQLAlchemy` initialization class](http://flask-sqlalchemy.pocoo.org/2.3/api/#flask_sqlalchemy.SQLAlchemy)
that configures Flask-SQLAlchemy.

The fixtures in this plugin depend on this `_db` fixture to access your
database and create nested transactions to run tests in. **You must define
this fixture in your `conftest.py` file for the plugin to work.**

An example setup that will produce a valid `_db` fixture could look like this
(this example comes from the [test setup](./tests/_conftest.py#L25-L61) for this repo):

```python
@pytest.fixture(scope='session')
def database(request):
    '''
    Create a Postgres database for the tests, and drop it when the tests are done.
    '''
    pg_host = DB_OPTS.get("host")
    pg_port = DB_OPTS.get("port")
    pg_user = DB_OPTS.get("username")
    pg_db = DB_OPTS["database"]

    init_postgresql_database(pg_user, pg_host, pg_port, pg_db)

    @request.addfinalizer
    def drop_database():
        drop_postgresql_database(pg_user, pg_host, pg_port, pg_db, 9.6)


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
```

Alternatively, if you already have a fixture that sets up database access for
your tests, you can define `_db` to return that fixture directly:

```python
@pytest.fixture(scope='session')
def database():
    # Set up all your database stuff here
    # ...
    return db

@pytest.fixture(scope='session')
def _db(database):
    return database
```

### Test configuration

This plugin allows you to configure a few different properties in a 
`setup.cfg` test configuration file in order to handle the specific database connection needs
of your app. For basic background on setting up pytest configuration files, see
the [pytest docs](https://docs.pytest.org/en/latest/customize.html#adding-default-options).

All three configuration properties ([`mocked-engines`](#mocked-engines),
[`mocked-sessions`](#mocked-sessions), and [`mocked-sessionmakers`](#mocked-sessionmakers))
work by **[patching](https://docs.python.org/3/library/unittest.mock.html#unittest.mock.patch)
one or more specified objects during a test**, replacing them with equivalent objects whose
database interactions will run inside of a transaction and ultimately be
rolled back when the test exits. Using these patches, you can call methods from
your codebase that alter database state with the knowledge that no changes will persist
beyond the body of the test.

The configured patches are applied in tests where either one of two conditions
are true:

1. a transactional fixture ([`db_session`](#db_session) or [`db_engine`](#db_engine))
is listed as a dependency, or
2. the [`@pytest.mark.transactional`](#using-the-transactional-mark)
mark is active.

#### `mocked-engines`

The `mocked-engines` property directs the plugin to [patch](https://docs.python.org/3/library/unittest.mock.html#unittest.mock.patch)
objects in your codebase, typically SQLAlchemy [Engine](http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine)
instances, replacing them with the [`db_engine` fixture](#db_engine) such that
any database updates performed by the objects get rolled back at the end of 
the test. 

The value for this property should be formatted as a whitespace-separated list 
of standard Python import paths, like `api.database.engine`. This property is **optional**.

Example:

```ini
[pytest]
mocked-engines=api.database.engine
```

To patch multiple objects at once, separate the paths with a whitespace:

```ini
[pytest]
mocked-engines=api.database.engine api.database.second_engine
```

#### `mocked-sessions`

The `mocked-sessions` property directs the plugin to [patch](https://docs.python.org/3/library/unittest.mock.html#unittest.mock.patch)
objects in your codebase, typically SQLAlchemy [Session](http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine)
instances, replacing them with the [`db_session`](#db_session) fixture such that
any database updates performed by the objects get rolled back at the end of 
the test. 

The value for this property should be formatted as a whitespace-separated list 
of standard Python import paths, like `api.database.db.session`. This property is **optional**.

Example:

```ini
[pytest]
mocked-sessions=api.database.db.session
```

To patch multiple objects at once, separate the paths with a whitespace:

```ini
[pytest]
mocked-sessions=api.database.db.session api.database.second_db.session
```

#### `mocked-sessionmakers`

The `mocked-sessionmakers` property directs the plugin to [patch](https://docs.python.org/3/library/unittest.mock.html#unittest.mock.patch)
objects in your codebase, typically [SQLAlchemy `sessionmaker`
factories](http://docs.sqlalchemy.org/en/latest/orm/session_api.html?highlight=sessionmaker#sqlalchemy.orm.session.sessionmaker),
replacing them with a mocked class that will return the transactional
[`db_session`](#db_session) fixture.

The value for this property should be formatted as a whitespace-separated list 
of standard Python import paths, like `api.database.WorkerSessionmaker`. This property is **optional**.

Example:

```ini
[pytest]
mocked-sessionmakers=api.database.WorkerSessionmaker
```

To patch multiple objects at once, separate the paths with a whitespace.

```ini
[pytest]
mocked-sessionmakers=api.database.WorkerSessionmaker api.database.SecondWorkerSessionmaker
```

## Fixtures

This plugin provides two fixtures for performing database updates inside nested
transactions that get rolled back at the end of a test: [`db_session`](#db_session) and
[`db_engine`](#db_engine). The fixtures provide similar functionality, but
with different APIs.

### `db_session`

The `db_session` fixture allows you to perform direct updates that will be
rolled back when the test exits. It exposes the same API as [SQLAlchemy's
`scoped_session` object](http://docs.sqlalchemy.org/en/latest/orm/contextual.html#sqlalchemy.orm.scoping.scoped_session).

Listing this fixture as a dependency will activate any mocks that are specified 
by the configuration properties [`mocked-engines`](#mocked-engines), [`mocked-sessions`](#mocked-sessions),
or [`mocked-sessionmakers`](#mocked-sessionmakers) in a configuration file.

Example:

```python
def test_a_transaction(db_session):
   row = db_session.query(Table).get(1) 
   row.name = 'testing'

   db_session.add(row)
   db_session.commit()

def test_transaction_doesnt_persist(db_session):
   row = db_session.query(Table).get(1) 
   assert row.name != 'testing'
```

### `db_engine`

Like [`db_session`](#db_session), the `db_engine` fixture allows you to perform direct updates
against the test database that will be rolled back when the test exits. It is
an instance of Python's built-in [`MagicMock`](https://docs.python.org/3/library/unittest.mock.html#unittest.mock.MagicMock)
class, with a spec set to match the API of [SQLAlchemy's
`Engine`](http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine) object.

Only a few `Engine` methods are exposed on this fixture:

- `db_engine.begin`: begin a new nested transaction ([API docs](http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine.begin))
- `db_engine.execute`: execute a raw SQL query ([API docs](http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine.execute)) 
- `db_engine.raw_connection`: return a raw DBAPI connection ([API docs](http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine.raw_connection)) 

Since `db_engine` is an instance of `MagicMock` with an `Engine` spec, other
methods of the `Engine` API can be called, but they will not perform any useful
work.

Listing this fixture as a dependency will activate any mocks that are specified 
by the configuration properties [`mocked-engines`](#mocked-engines),
[`mocked-sessions`](#mocked-sessions), or [`mocked-sessionmakers`](#mocked-sessionmakers)
in a configuration file.

Example:

```python
def test_a_transaction_using_engine(db_engine):
    with db_engine.begin() as conn:
        row = conn.execute('''UPDATE table SET name = 'testing' WHERE id = 1''')

def test_transaction_doesnt_persist(db_engine):
    row_name = db_engine.execute('''SELECT name FROM table WHERE id = 1''').fetchone()[0]
    assert row_name != 'testing' 
```

## Using the `transactional` mark

If you want to enforce transactional context but you don't need to use either
of the built-in transactional fixtures ([`db_session`](#db_session) or [`db_engine`](#db_engine)),
you can use the **`@pytest.mark.transactional`** decorator to mark that a test should
be run inside a transaction. For basic background on marks, see the [pytest
documentation](https://docs.pytest.org/en/latest/mark.html).

Note that since this approach assumes that you'll be performing database
updates using connections defined in your app, you **must** mock the
appropriate connections using the configuration properties [`mocked-sessions`](#mocked-sessions),
[`mocked-engines`](#mocked-engines), or [`mocked-sessionmakers`](#mocked-sessionmakers).
The `transactional` mark is, in essence, a way of triggering these mocks, so the mocks
themselves are necessary to create the transactional context that you expect.

Example:

```python
from api.database import db

@pytest.mark.transactional
def test_db_update():
    row = db.session.query(Table).get(1)
    row.name = 'testing'
    db.session.add(row)
    db.session.commit()

@pytest.mark.transactional
def test_db_update_doesnt_persist():
    row = db.session.query(Table).get(1)
    assert row.name != 'testing'
```

# Development

## Running the tests

Start by ensuring that all test requirements are installed:

```
pip install -U -r requirements/main.txt -r requirements/tests.txt
```

Next, install a development version of the plugin:

```
pip install -e .
```

Export a database connection string that the tests can use:

```
export TEST_DATABASE_URL=<db_connection_string>
```

Finally, run the tests using pytest:

```
pytest
```

## Acknowledgements

This plugin was initially developed for testing
[Dedupe.io](https://dedupe.io), a web app for record linkage and entity
resolution using machine learning. Dedupe.io is built and maintained
by [DataMade](https://datamade.us).

The code is greatly indebted to [Alex Michael](https://github.com/alexmic),
whose blog post ["Delightful testing with pytest and
Flask-SQLAlchemy"](http://alexmic.net/flask-sqlalchemy-pytest/) helped
establish the basic approach on which this plugin builds.

## Copyright

Copyright (c) 2018 Jean Cochrane and DataMade. Released under the MIT License.

Third-party copyright in this distribution is noted where applicable.
