# pytest-flask-sqlalchemy-transactions

A [pytest](https://docs.pytest.org/en/latest/) plugin providing fixtures for running tests in
transactions using Flask and SQLAlchemy.

## Motivation

Inspired by [Django's built-in support for transactional
tests](https://jeancochrane.com/blog/django-test-transactions), this plugin 
seeks to provide comprehensive, easy-to-use fixtures for wrapping tests in
database transactions using Pytest, Flask, and SQLAlchemy.

In order to test database operations in the context of stateful web applications,
developers must pay an inordinate amount of attention to the database changes incurred by their
tests, since unanticipated changes can leak state between tests and inhibit
test isolation. While some test engineers advocate avoiding database
interactions entirely (see Harry Percival's ["Fast Tests, Slow Tests, and Hot
Lava"](https://www.obeythetestinggoat.com/book/chapter_hot_lava.html) for more
on this perspective), this approach is infeasible in data-intensive web applications,
where much of the business logic involves state changes to a database. For
these kinds of applications, a solution is needed that will allow the developer
to trigger and verify database updates while still ensuring test isolation.

The goal of this plugin is to make testing stateful Flask applications easier
by providing fixtures that permit the developer to **make arbitrary
database updates with the confidence that any changes made during a test will
roll back** once the test exits.

## Quick examples

Use the `db_session` fixture to make **database updates that won't persist beyond
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

The `db_engine` fixture works the same way, but **copies the API of
SQLAlchemy's [Engine
object](http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine)**.

```python
def test_a_transaction_using_engine(db_engine):
    with db_engine.begin() as conn:
        row = conn.execute('''UPDATE table SET name = 'testing' WHERE id = 1''')

def test_transaction_doesnt_persist(db_engine):
    row_name = db_engine.execute('''SELECT name FROM table WHERE id = 1''').fetchone()[0]
    assert row_name != 'testing' 
```

Use configuration properties to **mock database connections in an app with fixtures that enforce
nested transactions**, allowing any method from the codebase to run inside
a test that imports a transactional fixture (`db_session` or `db_engine`) with
the assurance that any database changes made will be rolled back at the end of the test:

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

# Usage

## Installation

### From PyPi

Install using pip:

```
pip install pytest-flask-sqlalchemy-transactions
```

### Development version

Clone the repo from GitHub and switch into the new directory:

```
git clone git@github.com:jeancochrane/pytest-flask-sqlalchemy-transactions.git
```

You can install using pip if you'd like:

```
pip install -e .
```

Or install the plugin dependencies manually:

```
pip install -r requirements/main.txt
```

## Configuration

This plugin requires that you set up a test configuration file with a few
specific properties under the `[pytest]` section. For background on pytest
configuration, see the [pytest docs](https://docs.pytest.org/en/latest/customize.html#adding-default-options).

### `db-connection-string`

The `db-connection-string` property allows the plugin to access a test
database. **This property is required.** 

Example:

```ini
[pytest]
db-connection-string=postgresql://postgres@localhost:5432/pytest_test
```

### `mocked-engines`

The `mocked-engines` property directs the plugin to [patch](https://docs.python.org/3/library/unittest.mock.html#unittest.mock.patch)
objects in your codebase, typically SQLAlchemy [Engine](http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine)
instances, replacing them with the `db_engine` fixture in tests where either
of the transactional fixtures (`db_session` or `db_engine`) are listed as dependencies.
Objects should be formatted as standard Python import paths, like `api.database.engine`.
This property is optional.

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

### `mocked-sessions`

The `mocked-sessions` property directs the plugin to [patch](https://docs.python.org/3/library/unittest.mock.html#unittest.mock.patch)
objects in your codebase, typically SQLAlchemy [Session](http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine)
instances, replacing them with the `db_session` fixture in tests where either
of the transactional fixtures (`db_session` or `db_engine`) are listed as dependencies.
Objects should be formatted as standard Python import paths, like `api.database.db.session`.
This property is optional.

To patch multiple objects at once, separate the paths with a whitespace.

Example:

```ini
[pytest]
mocked-sessions=api.database.db.session
```

### `mocked-sessionmakers`

The `mocked-sessionmakers` property directs the plugin to [patch](https://docs.python.org/3/library/unittest.mock.html#unittest.mock.patch)
objects in your codebase, typically SQLAlchemy [sessionmaker](http://docs.sqlalchemy.org/en/latest/orm/session_api.html?highlight=sessionmaker#sqlalchemy.orm.session.sessionmaker)
factories, replacing them with a mocked class that will return the `db_session` fixture
in tests where either of the transactional fixtures (`db_session` or `db_engine`)
are listed as dependencies. Objects should be formatted as standard Python import paths,
like `api.database.WorkerSessionmaker`. This property is optional.

To patch multiple objects at once, separate the paths with a whitespace.

Example:

```ini
[pytest]
mocked-sessionmakers=api.database.WorkerSessionmaker
```

## Fixtures

This plugin provides two fixtures for performing database updates inside nested
transactions that get rolled back at the end of a test: `db_engine` and
`db_session`. In addition, the plugin provides a fixture for direct database
changes that will not get rolled back: `module_engine`. This fixture can be
useful for setting up module- or session-scoped state.

### `db_session`

The `db_session` fixture allows you to perform direct updates that will be
rolled back when the test exits. It exposes the same API as [SQLAlchemy's
`scoped_session` object](http://docs.sqlalchemy.org/en/latest/orm/contextual.html#sqlalchemy.orm.scoping.scoped_session).

Listing this fixture as a dependency will activate any mocks that are specified 
by the configuration properties `mocked-engines`, `mocked-sessions`, or
`mocked-sessionmakers` in a configuration file.

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

Like `db_session`, the `db_engine` fixture allows you to perform direct updates
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
by the configuration properties `mocked-engines`, `mocked-sessions`, or
`mocked-sessionmakers` in a configuration file.

Example:

```python
def test_a_transaction_using_engine(db_engine):
    with db_engine.begin() as conn:
        row = conn.execute('''UPDATE table SET name = 'testing' WHERE id = 1''')

def test_transaction_doesnt_persist(db_engine):
    row_name = db_engine.execute('''SELECT name FROM table WHERE id = 1''').fetchone()[0]
    assert row_name != 'testing' 
```

### `module_engine` 

In contrast to `db_session` and `db_engine`, the `module_engine` fixture does
not wrap its test in a database transaction. Instead, this fixture returns a
SQLAlchemy `Engine` object that can be used to set up persistent state in tests
or fixtures. Its API is identical to the [SQLAlchemy `Engine`
API](http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine).

Listing this fixture as a dependency **will not** activate any mocks that are specified 
by the configuration properties `mocked-engines`, `mocked-sessions`, or
`mocked-sessionmakers` in a configuration file.

Example:

```python
def test_module_engine(module_engine):
    with module_engine.begin() as conn:
        row = conn.execute('''UPDATE table SET name = 'testing' WHERE id = 1''')

def test_module_engine_changes_persist(db_engine):
    row_name = db_engine.execute('''SELECT name FROM table WHERE id = 1''').fetchone()[0]
    assert row_name == 'testing' 
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
