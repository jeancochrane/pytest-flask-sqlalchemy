import os
import contextlib

import pytest
import sqlalchemy as sa
from packaging import version


@pytest.fixture(scope='module')
def _db():
    '''
    A user-defined _db fixture is required to provide the plugin with a SQLAlchemy
    Session object that can access the test database. If the user hasn't defined
    that fixture, raise an error.
    '''
    msg = ("_db fixture not defined. The pytest-flask-sqlalchemy plugin " +
           "requires you to define a _db fixture that returns a SQLAlchemy Session " +
           "with access to your test database. For more information, see the plugin " +
           "documentation: " +
           "https://github.com/jeancochrane/pytest-flask-sqlalchemy#conftest-setup")

    raise NotImplementedError(msg)


@pytest.fixture(scope='function')
def _transaction(request, _db, mocker):
    '''
    Create a transactional context for tests to run in.
    '''
    # Start a transaction
    connection = _db.engine.connect()
    transaction = connection.begin()

    # Bind a session to the transaction. The empty `binds` dict is necessary
    # when specifying a `bind` option, or else Flask-SQLAlchemy won't scope
    # the connection properly
    options = dict(bind=connection, binds={})
    session = _db.create_scoped_session(options=options)

    # Make sure the session, connection, and transaction can't be closed by accident in
    # the codebase
    connection.force_close = connection.close
    transaction.force_rollback = transaction.rollback

    connection.close = lambda: None
    transaction.rollback = lambda: None
    session.close = lambda: None

    # Begin a nested transaction (any new transactions created in the codebase
    # will be held until this outer transaction is committed or closed)
    session.begin_nested()

    # Each time the SAVEPOINT for the nested transaction ends, reopen it
    @sa.event.listens_for(session, 'after_transaction_end')
    def restart_savepoint(session, trans):
        if trans.nested and not trans._parent.nested:
            # ensure that state is expired the way
            # session.commit() at the top level normally does
            session.expire_all()

            session.begin_nested()

    # Force the connection to use nested transactions
    connection.begin = connection.begin_nested

    # If an object gets moved to the 'detached' state by a call to flush the session,
    # add it back into the session (this allows us to see changes made to objects
    # in the context of a test, even when the change was made elsewhere in
    # the codebase)
    @sa.event.listens_for(session, 'persistent_to_detached')
    @sa.event.listens_for(session, 'deleted_to_detached')
    def rehydrate_object(session, obj):
        session.add(obj)

    @request.addfinalizer
    def teardown_transaction():
        # Delete the session
        session.remove()

        # Rollback the transaction and return the connection to the pool
        transaction.force_rollback()
        connection.force_close()

    return connection, transaction, session


@pytest.fixture(scope='function')
def _engine(pytestconfig, request, _transaction, mocker):
    '''
    Mock out direct access to the semi-global Engine object.
    '''
    connection, _, session = _transaction

    # Make sure that any attempts to call `connect()` simply return a
    # reference to the open connection
    engine = mocker.MagicMock(spec=sa.engine.Engine)

    engine.connect.return_value = connection

    # Threadlocal engine strategies were deprecated in SQLAlchemy 1.3, which
    # resulted in contextual_connect becoming a private method. See:
    # https://docs.sqlalchemy.org/en/latest/changelog/migration_13.html
    if version.parse(sa.__version__) < version.parse('1.3'):
        engine.contextual_connect.return_value = connection
    else:
        engine._contextual_connect.return_value = connection

    # References to `Engine.dialect` should redirect to the Connection (this
    # is primarily useful for the `autoload` flag in SQLAlchemy, which references
    # the Engine dialect to reflect tables)
    engine.dialect = connection.dialect

    @contextlib.contextmanager
    def begin():
        '''
        Open a new nested transaction on the `connection` object.
        '''
        with connection.begin_nested():
            yield connection

    # Force the engine object to use the current connection and transaction
    engine.begin = begin
    engine.execute = connection.execute

    # Enforce nested transactions for raw DBAPI connections
    def raw_connection():
        # Start a savepoint
        connection.execute('''SAVEPOINT raw_conn''')

        # Preserve close/commit/rollback methods
        connection.connection.force_close = connection.connection.close
        connection.connection.force_commit = connection.connection.commit
        connection.connection.force_rollback = connection.connection.rollback

        # Prevent the connection from being closed accidentally
        connection.connection.close = lambda: None
        connection.connection.commit = lambda: None
        connection.connection.set_isolation_level = lambda level: None

        # If a rollback is initiated, return to the original savepoint
        connection.connection.rollback = lambda: connection.execute('''ROLLBACK TO SAVEPOINT raw_conn''')

        return connection.connection

    engine.raw_connection = raw_connection

    for mocked_engine in pytestconfig._mocked_engines:
        mocker.patch(mocked_engine, new=engine)

    session.bind = engine

    @request.addfinalizer
    def reset_raw_connection():
        # Return the underlying connection to its original state if it has changed
        if hasattr(connection.connection, 'force_rollback'):
            connection.connection.commit = connection.connection.force_commit
            connection.connection.rollback = connection.connection.force_rollback
            connection.connection.close = connection.connection.force_close

    return engine


@pytest.fixture(scope='function')
def _session(pytestconfig, _transaction, mocker):
    '''
    Mock out Session objects (a common way of interacting with the database using
    the SQLAlchemy ORM) using a transactional context.
    '''
    _, _, session = _transaction

    # Whenever the code tries to access a Flask session, use the Session object
    # instead
    for mocked_session in pytestconfig._mocked_sessions:
        mocker.patch(mocked_session, new=session)

    # Create a dummy class to mock out the sessionmakers
    # (We need to do this as a class because we can't mock __call__ methods)
    class FakeSessionMaker(sa.orm.Session):
        def __call__(self):
            return session

        @classmethod
        def configure(cls, *args, **kwargs):
            pass

    # Mock out the WorkerSession
    for mocked_sessionmaker in pytestconfig._mocked_sessionmakers:
        mocker.patch(mocked_sessionmaker, new_callable=FakeSessionMaker)

    return session


@pytest.fixture(scope='function')
def db_session(_engine, _session, _transaction):
    '''
    Make sure all the different ways that we access the database in the code
    are scoped to a transactional context, and return a Session object that
    can interact with the database in the tests.

    Use this fixture in tests when you would like to use the SQLAlchemy ORM
    API, just as you might use a SQLAlchemy Session object.
    '''
    return _session


@pytest.fixture(scope='function')
def db_engine(_engine, _session, _transaction):
    '''
    Make sure all the different ways that we access the database in the code
    are scoped to a transactional context, and return an alias for the
    transactional Engine object that can interact with the database in the tests.

    Use this fixture in tests when you would like to run raw SQL queries using the
    SQLAlchemy Engine API.
    '''
    return _engine
