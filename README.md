# pytest-flask-sqlalchemy

A [pytest](https://docs.pytest.org/en/latest/) plugin providing fixtures for running tests in
transactions using [Flask-SQLAlchemy](http://flask-sqlalchemy.pocoo.org/latest/).

## Contents

- [**Motivation**](#motivation)
- [**Quick examples**](#quick-examples)
- [**Usage**](#usage)
    - [Installation](#installation)
        - [From PyPi](#from-pypi)
        - [Development version](#development-version)
        - [Supported backends](#supported-backends)
    - [Configuration](#configuration)
        - [Conftest setup](#conftest-setup)
        - [Test configuration](#test-configuration)
            - [`mocked-engines`](#mocked-engines)
            - [`mocked-sessions`](#mocked-sessions)
            - [`mocked-sessionmakers`](#mocked-sessionmakers)
        - [Writing transactional tests](#writing-transactional-tests)
    - [Fixtures](#fixtures)
        - [`db_session`](#db_session)
        - [`db_engine`](#db_engine)
    - [Enabling transactions without fixtures](#enabling-transactions-without-fixtures)
- [**Development**](#development)
    - [Running the tests](#running-the-tests)
    - [Acknowledgements](#acknowledgements)
    - [Copyright](#copyright)

## <a name="motivation"></a>Motivation

Inspired by [Django's built-in support for transactional
tests](https://jeancochrane.com/blog/django-test-transactions), this plugin 
seeks to provide comprehensive, easy-to-use Pytest fixtures for wrapping tests in
database transactions for [Flask-SQLAlchemy](http://flask-sqlalchemy.pocoo.org/latest/)
apps. The goal is to make testing stateful Flask-SQLAlchemy applications easier by
providing fixtures that permit the developer to **make arbitrary database updates
with the confidence that any changes made during a test will roll back** once the test exits.

## <a name="quick-examples"></a>Quick examples

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
# In setup.cfg

[tool:pytest]
mocked-sessions=database.db.session
mocked-engines=database.engine
```

```python
# In database.py

db = flask_sqlalchemy.SQLAlchemy()
engine = sqlalchemy.create_engine('DATABASE_URI')
```

```python
# In models.py

class Table(db.Model):
    __tablename__ = 'table'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))

    def set_name(new_name):
        self.name = new_name
        db.session.add(self)
        db.session.commit()
```

```python
# In tests/test_set_name.py

def test_set_name(db_session):
    row = db_session.query(Table).get(1)
    row.set_name('testing')
    assert row.name == 'testing'

def test_transaction_doesnt_persist(db_session):
   row = db_session.query(Table).get(1) 
   assert row.name != 'testing'
```

# <a name="usage"></a>Usage

## <a name="installation"></a>Installation

### <a name="from-pypi"></a>From PyPi

Install using pip:

```
pip install pytest-flask-sqlalchemy
```

Once installed, pytest will detect the plugin automatically during test collection.
For basic background on using third-party plugins with pytest, see the [pytest
documentation](https://docs.pytest.org/en/latest/plugins.html?highlight=plugins).

### <a name="development-version"></a>Development version

Clone the repo from GitHub and switch into the new directory:

```
git clone git@github.com:jeancochrane/pytest-flask-sqlalchemy.git
cd pytest-flask-sqlalchemy
```

You can install using pip:

```
pip install .
```

### <a name="supported-backends"></a>Supported backends

So far, pytest-flask-sqlalchemy has been most extensively tested against
PostgreSQL 9.6. It should theoretically work with any backend that is supported
by SQLAlchemy, but Postgres is the only backend that is currently tested by the
test suite.

Official support for SQLite and MySQL is [planned for a future
release](https://github.com/jeancochrane/pytest-flask-sqlalchemy/issues/3).
In the meantime, if you're using one of those backends and you run in to
problems, we would greatly appreciate your help! [Open an
issue](https://github.com/jeancochrane/pytest-flask-sqlalchemy/issues/new) if
something isn't working as you expect.

## <a name="configuration"></a>Configuration

### <a name="conftest-setup"></a>Conftest setup

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

### <a name="test-configuration"></a>Test configuration

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

The configured patches are only applied in tests where a transactional fixture
(either [`db_session`](#db_session) or [`db_engine`](#db_engine)) is included
in the test function arguments.

#### <a name="mocked-engines"></a>`mocked-engines`

The `mocked-engines` property directs the plugin to [patch](https://docs.python.org/3/library/unittest.mock.html#unittest.mock.patch)
objects in your codebase, typically SQLAlchemy [Engine](http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine)
instances, replacing them with the [`db_engine` fixture](#db_engine) such that
any database updates performed by the objects get rolled back at the end of 
the test. 

The value for this property should be formatted as a whitespace-separated list 
of standard Python import paths, like `database.engine`. This property is **optional**.

Example:

```python
# In database.py

engine = sqlalchemy.create_engine(DATABASE_URI)
```

```ini
# In setup.cfg

[tool:pytest]
mocked-engines=database.engine
```

To patch multiple objects at once, separate the paths with a whitespace:

```ini
# In setup.cfg

[tool:pytest]
mocked-engines=database.engine database.second_engine
```

#### <a name="mocked-sessions"></a>`mocked-sessions`

The `mocked-sessions` property directs the plugin to [patch](https://docs.python.org/3/library/unittest.mock.html#unittest.mock.patch)
objects in your codebase, typically SQLAlchemy [Session](http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine)
instances, replacing them with the [`db_session`](#db_session) fixture such that
any database updates performed by the objects get rolled back at the end of 
the test. 

The value for this property should be formatted as a whitespace-separated list 
of standard Python import paths, like `database.db.session`. This property is **optional**.

Example:

```python
# In database.py

db = SQLAlchemy()
```

```ini
# In setup.cfg

[tool:pytest]
mocked-sessions=database.db.session
```

To patch multiple objects at once, separate the paths with a whitespace:

```ini
# In setup.cfg

[tool:pytest]
mocked-sessions=database.db.session database.second_db.session
```

#### <a name="mocked-sessionmakers"></a>`mocked-sessionmakers`

The `mocked-sessionmakers` property directs the plugin to [patch](https://docs.python.org/3/library/unittest.mock.html#unittest.mock.patch)
objects in your codebase, typically instances of [SQLAlchemy's `sessionmaker`
factory](http://docs.sqlalchemy.org/en/latest/orm/session_api.html?highlight=sessionmaker#sqlalchemy.orm.session.sessionmaker),
replacing them with a mocked class that will return the transactional
[`db_session`](#db_session) fixture. This can be useful if you have
pre-configured instances of sessionmaker objects that you import in the code
to spin up sessions on the fly.

The value for this property should be formatted as a whitespace-separated list 
of standard Python import paths, like `database.WorkerSessionmaker`. This property is **optional**.

Example:

```python
# In database.py

WorkerSessionmaker = sessionmaker()
```

```ini
[tool:pytest]
mocked-sessionmakers=database.WorkerSessionmaker
```

To patch multiple objects at once, separate the paths with a whitespace.

```ini
[tool:pytest]
mocked-sessionmakers=database.WorkerSessionmaker database.SecondWorkerSessionmaker
```

### <a name="writing-transactional-tests"></a>Writing transactional tests

Once you have your [conftest file set up](#conftest-setup) and you've [overridden the
necessary connectables in your test configuration](#test-configuration), you're ready
to write some transactional tests. Simply import one of the module's [transactional
fixtures](#fixtures) in your test signature, and the test will be wrapped in a transaction.

Note that by default, **tests are only wrapped in transactions if they import one of
the [transactional fixtures](#fixtures) provided by this module.** Tests that do not
import the fixture will interact with your database without opening a transaction:

```python
# This test will be wrapped in a transaction.
def transactional_test(db_session):
    ...
    
# This test **will not** be wrapped in a transaction, since it does not import a
# transactional fixture.
def non_transactional_test():
    ...
```

The fixtures provide a way for you to control which tests require transactions and
which don't. This is often useful, since avoiding transaction setup can speed up
tests that don't interact with your database.

For more information about the transactional fixtures provided by this module, read on
to the [fixtures section](#fixtures). For guidance on how to automatically enable
transactions without having to specify fixtures, see the section on [enabling transactions
without fixtures](#enabling-transactions-without-fixtures).

## <a name="fixtures"></a>Fixtures

This plugin provides two fixtures for performing database updates inside nested
transactions that get rolled back at the end of a test: [`db_session`](#db_session) and
[`db_engine`](#db_engine). The fixtures provide similar functionality, but
with different APIs.

### <a name="db_session"></a>`db_session`

The `db_session` fixture allows you to perform direct updates that will be
rolled back when the test exits. It exposes the same API as [SQLAlchemy's
`scoped_session` object](http://docs.sqlalchemy.org/en/latest/orm/contextual.html#sqlalchemy.orm.scoping.scoped_session).

Including this fixture as a function argument of a test will activate any mocks that are defined
by the configuration properties [`mocked-engines`](#mocked-engines), [`mocked-sessions`](#mocked-sessions),
or [`mocked-sessionmakers`](#mocked-sessionmakers) in the test configuration file for
the duration of that test.

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

### <a name="db_engine"></a>`db_engine`

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

Including this fixture as a function argument of a test will activate any mocks that are defined
by the configuration properties [`mocked-engines`](#mocked-engines), [`mocked-sessions`](#mocked-sessions),
or [`mocked-sessionmakers`](#mocked-sessionmakers) in the test configuration file for
the duration of that test.

Example:

```python
def test_a_transaction_using_engine(db_engine):
    with db_engine.begin() as conn:
        row = conn.execute('''UPDATE table SET name = 'testing' WHERE id = 1''')

def test_transaction_doesnt_persist(db_engine):
    row_name = db_engine.execute('''SELECT name FROM table WHERE id = 1''').fetchone()[0]
    assert row_name != 'testing' 
```

## <a name="enabling-transactions-without-fixtures"></a>Enabling transactions without fixtures

If you know you want to make all of your tests transactional, it can be annoying to have
to specify one of the [fixtures](#fixtures) in every test signature.

The best way to automatically enable transactions without having to include an extra fixture
in every test is to wire up an
[autouse fixture](https://docs.pytest.org/en/latest/fixture.html#autouse-fixtures-xunit-setup-on-steroids)
for your test suite. This can be as simple as:

```python
# Automatically enable transactions for all tests, without importing any extra fixtures.
@pytest.fixture(autouse=True)
def enable_transactional_tests(db_session):
    pass
```

In this configuration, the `enable_transactional_tests` fixture will be automatically used in
all tests, meaning that `db_session` will also be used. This way, all tests will be wrapped
in transactions without having to explicitly require either `db_session` or `enable_transactional_tests`.

# <a name="development"></a>Development

## <a name="running-the-tests"></a>Running the tests

To run the tests, start by installing a development version of the plugin that
includes test dependencies:

```
pip install -e .[tests]
```

Next, export a [database connection string](http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls)
that the tests can use (the database referenced by the string will be created
during test setup, so it does not need to exist):

```
export TEST_DATABASE_URL=<db_connection_string>
```

Finally, run the tests using pytest:

```
pytest
```

## <a name="acknowledgements"></a>Acknowledgements

This plugin was initially developed for testing
[Dedupe.io](https://dedupe.io), a web app for record linkage and entity
resolution using machine learning. Dedupe.io is built and maintained
by [DataMade](https://datamade.us).

The code is greatly indebted to [Alex Michael](https://github.com/alexmic),
whose blog post ["Delightful testing with pytest and
Flask-SQLAlchemy"](http://alexmic.net/flask-sqlalchemy-pytest/) helped
establish the basic approach on which this plugin builds.

Many thanks to [Igor Ghisi](https://github.com/igortg/), who donated the PyPi
package name. Igor had been working on a similar plugin and proposed combining
efforts. Thanks to Igor, the plugin name is much stronger.

## <a name="copyright"></a>Copyright

Copyright (c) 2019 Jean Cochrane and DataMade. Released under the MIT License.

Third-party copyright in this distribution is noted where applicable.
