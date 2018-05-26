# pytest-flask-sqlalchemy-transactions

Run tests in transactions using Pytest, Flask, and SQLAlchemy.

# Running tests

```
pip install -U -r requirements/main.txt -r requirements/tests.txt
pip install -e .
export TEST_DATABASE_URL=<db_connection_string>
pytest
```
