# pytest-flask-sqlalchemy-transactions

A [pytest](https://docs.pytest.org/en/latest/) plugin providing fixtures for running tests in
transactions using Flask and SQLAlchemy.

## Motivation

Inspired by [Django's built-in support for transactional
tests](https://jeancochrane.com/blog/django-test-transactions), this plugin 
seeks to provide comprehensive, easy-to-use fixtures for wrapping tests in
database transactions using Pytest, Flask, and SQLAlchemy.

## Quick examples

Use the `db_session` fixture to make **database updates that won't persist beyond
the body of the test**:

```python
from api.models import Table

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

## API

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
