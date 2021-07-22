def test_mocked_engines(db_testdir):
    '''
    Test that we can specify paths to specific Engine objects that the plugin
    will mock.
    '''
    db_testdir.makeini("""
        [pytest]
        mocked-engines=collections.namedtuple collections.deque
    """)

    db_testdir.makepyfile("""
        def test_mocked_engines(db_engine):
            from collections import namedtuple, deque
            assert str(namedtuple).startswith("<MagicMock spec='Engine'")
            assert str(deque).startswith("<MagicMock spec='Engine'")
    """)

    result = db_testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_mocked_sessions(db_testdir):
    '''
    Test that we can specify paths to specific Session objects that the plugin
    will mock.
    '''
    db_testdir.makeini("""
        [pytest]
        mocked-sessions=collections.namedtuple collections.Counter
    """)

    db_testdir.makepyfile("""
        def test_mocked_sessions(db_session):
            from collections import namedtuple, Counter
            assert str(namedtuple).startswith("<sqlalchemy.orm.scoping.scoped_session object")
            assert str(Counter).startswith("<sqlalchemy.orm.scoping.scoped_session object")
    """)

    result = db_testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_mocked_sessionmakers(db_testdir):
    '''
    Test that we can specify paths to specific Sessionmaker objects that the plugin
    will mock.
    '''
    db_testdir.makeini("""
        [pytest]
        mocked-sessionmakers=collections.namedtuple collections.Counter
    """)

    db_testdir.makepyfile("""
        def test_mocked_sessionmakers(db_session):
            from collections import namedtuple, Counter
            assert str(namedtuple).startswith("<pytest_flask_sqlalchemy.fixtures._session.<locals>.FakeSessionMaker")
            assert str(Counter).startswith("<pytest_flask_sqlalchemy.fixtures._session.<locals>.FakeSessionMaker")
    """)

    result = db_testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_missing_db_fixture(testdir):
    '''
    Test that in the case where the user neglects to define a _db fixture, any
    tests requiring transactional context will raise an error.
    '''
    # Create a conftest file that is missing a _db fixture but is otherwise
    # valid for a Flask-SQLAlchemy test suite
    conftest = """
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

            janitor = DatabaseJanitor(pg_user, pg_host, pg_port, pg_db, 9.6, pg_pass)
            janitor.init()
            yield
            janitor.drop()



        @pytest.fixture(scope='session')
        def app(database):
            '''
            Create a Flask app context for the tests.
            '''
            app = Flask(__name__)

            app.config['SQLALCHEMY_DATABASE_URI'] = DB_CONN

            return app
    """

    testdir.makeconftest(conftest)

    # Define a test that will always pass, assuming that fixture setup works
    testdir.makepyfile("""
        def test_missing_db_fixture(db_session):
            assert True
    """)

    result = testdir.runpytest()
    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines([
        '*NotImplementedError: _db fixture not defined*'
    ])
