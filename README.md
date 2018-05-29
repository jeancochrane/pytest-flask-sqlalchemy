# pytest-flask-sqlalchemy-transactions

A [pytest](https://docs.pytest.org/en/latest/) plugin providing fixtures for running tests in
transactions using Flask and SQLAlchemy.

## Motivation

Inspired by [Django's built-in support for transactional
tests](https://jeancochrane.com/blog/django-test-transactions), this plugin 
seeks to provide comprehensive, easy-to-use fixtures for wrapping tests in
database transactions using Pytest, Flask, and SQLAlchemy.

The goal of this plugin is to make testing stateful applications easier by
allowing the developer to **make arbitrary database updates with
the confidence that any changes you make will be rolled back** once the test
exits.

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

Use configuration variables to **mock database connections in an app with fixtures that enforce
nested transactions**, allowing any method from the codebase to run without
leaking database state between tests:

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
# tests/tox.ini

[pytest]
mocked-sessions=api.database.db.session
mocked-engines=api.database.engine
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

```python
[pytest]
db-connection-string=postgresql://postgres@localhost:5432/pytest_test
```

### `mocked-engines`

The `mocked-engines` property directs the plugin to [patch](https://docs.python.org/3/library/unittest.mock.html#unittest.mock.patch)
objects in your codebase, typically SQLAlchemy [Engine](http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine)
instances, replacing them with the `db_engine` fixture. Objects
should be formatted as a standard import string, like `api.database.engine`.
This property is optional.

Example:

```python
[pytest]
mocked-engines=api.database.engine
```

To patch multiple objects at once, separate them with a whitespace:

```python
[pytest]
mocked-engines=api.database.engine api.database.second_engine
```

### `mocked-sessions`

The `mocked-sessions` property directs the plugin to [patch](https://docs.python.org/3/library/unittest.mock.html#unittest.mock.patch)
objects in your codebase, typically SQLAlchemy [Session](http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine)
instances, replacing them with the `db_session` fixture. Objects
should be formatted as a standard import string, like `api.database.db.session`.
This property is optional.

To patch multiple objects at once, separate them with a whitespace.

Example:

```
[pytest]
mocked-sessions=api.database.db.session
```

### `mocked-sessionmakers`

The `mocked-sessionmakers` property directs the plugin to [patch](https://docs.python.org/3/library/unittest.mock.html#unittest.mock.patch)
objects in your codebase, typically SQLAlchemy [sessionmaker](http://docs.sqlalchemy.org/en/latest/orm/session_api.html?highlight=sessionmaker#sqlalchemy.orm.session.sessionmaker)
factories, replacing them with a mocked class that will return the `db_session` fixture
when configured. Objects should be formatted as a standard import string,
like `api.database.WorkerSessionmaker`. This property is optional.

To patch multiple objects at once, separate them with a whitespace.

Example:

```
[pytest]
mocked-sessionmakers=api.database.WorkerSessionmaker
```

## Fixtures

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

This library was initially developed for testing
[Dedupe.io](https://dedupe.io), a web app for record linkage and entity
resolution using machine learning. Dedupe.io is built and maintained
by [DataMade](https://datamade.us).

The code is greatly indebted to [Alex Michael](https://github.com/alexmic),
whose blog post ["Delightful testing with pytest and
Flask-SQLAlchemy"](http://alexmic.net/flask-sqlalchemy-pytest/) helped
establish the basic approach on which this library builds.

## Copyright

Copyright (c) 2018 Jean Cochrane and DataMade. Released under the MIT License.

Third-party copyright in this distribution is noted where applicable.
