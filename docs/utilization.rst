-----
Usage
-----

Configuration
=============

.. _conftest-setup:

Conftest Setup
--------------

This plugin assumes that a fixture called `_db` has been defined in the root conftest file for your tests.
The `_db` fixture should expose access to a valid SQLAlchemy `Session object <http://docs.sqlalchemy.org/en/latest/orm/session_api.html?highlight=session#sqlalchemy.orm.session.Session>`_ that can interact with your database,
for example via the `SQLAlchemy initialization class <http://flask-sqlalchemy.pocoo.org/2.3/api/#flask_sqlalchemy.SQLAlchemy>`_ that configures Flask-SQLAlchemy.

The fixtures in this plugin depend on this ``_db`` fixture to access your database and create nested transactions to run tests in.
**You must define this fixture in your `conftest.py` file for the plugin to work.**

An example setup that will produce a valid ``_db`` fixture could look like this (this example comes from the :ref:`test setup <test-setup>` for this repo):

.. literalinclude:: ../tests/_conftest.py
    :name: test setup:database
    :lines: 25-39

..    @pytest.fixture(scope='session')
..    def database(request):
..        '''
..        Create a Postgres database for the tests, and drop it when the tests are done.
..        '''
..        pg_host = DB_OPTS.get("host")
..        pg_port = DB_OPTS.get("port")
..        pg_user = DB_OPTS.get("username")
..        pg_db = DB_OPTS["database"]
..
..        init_postgresql_database(pg_user, pg_host, pg_port, pg_db)
..
..        @request.addfinalizer
..        def drop_database():
..            drop_postgresql_database(pg_user, pg_host, pg_port, pg_db, 9.6)

.. literalinclude:: ../tests/_conftest.py
    :name: test setup:app
    :lines: 42-51

..    @pytest.fixture(scope='session')
..    def app(database):
..        '''
..        Create a Flask app context for the tests.
..        '''
..        app = Flask(__name__)
..        app.config['SQLALCHEMY_DATABASE_URI'] = DB_CONN
..        return app


.. literalinclude:: ../tests/_conftest.py
    :name: test setup:_db
    :lines: 53-61

..    @pytest.fixture(scope='session')
..    def _db(app):
..        '''
..        Provide the transactional fixtures with access to the database via a Flask-SQLAlchemy
..        database connection.
..        '''
..        db = SQLAlchemy(app=app)
..
..        return db


Alternatively, if you already have a fixture that sets up database access for
your tests, you can define `_db` to return that fixture directly:

.. code-block::

    @pytest.fixture(scope='session')
    def database():
        # Set up all your database stuff here
        # ...
        return db

    @pytest.fixture(scope='session')
    def _db(database):
        return database

.. _test-configuration:

Test configuration
------------------

This plugin allows you to configure a few different properties in a :file:`setup.cfg` test configuration file in order to handle the specific database connection needs of your app.
For basic background on setting up pytest configuration files, see the `pytest docs <https://docs.pytest.org/en/latest/customize.html#adding-default-options>`_.

All three configuration properties (:ref:`mocked-engines <mocked-engines>`), :ref:`mocked-sessions <mocked-sessions>`, and :ref:`mocked-sessionmakers <mocked-sessionmakers>`)
work by `patching <https://docs.python.org/3/library/unittest.mock.html#unittest.mock.patch>`_ **one or more specified objects during a test**,
replacing them with equivalent objects whose database interactions will run inside of a transaction and ultimately be rolled back when the test exits.
Using these patches, you can call methods from your codebase that alter database state with the knowledge that no changes will persist beyond the body of the test.

The configured patches are only applied in tests where a transactional fixture (either :ref:`db_session <db_session>` or :ref:`db_engine <db_engine>`) is included in the test function arguments.

.. _mocked-engines:

``mocked-engines``
~~~~~~~~~~~~~~~~~~

The `mocked-engines` property directs the plugin to `patch <https://docs.python.org/3/library/unittest.mock.html#unittest.mock.patch>`_ objects in your codebase, typically SQLAlchemy `Engine <http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine>`_ instances,
replacing them with the :ref:`db_engine fixture <db_engine>` such that any database updates performed by the objects get rolled back at the end of the test.

The value for this property should be formatted as a whitespace-separated list of standard Python import paths, like `database.engine`. This property is **optional**.

.. rubric:: Example:

.. code-block:: Python
    :caption: :file:`database.py`

    engine = sqlalchemy.create_engine(DATABASE_URI)

.. code-block:: ini
    :caption: :file:`setup.cfg`

    [tool:pytest]
    mocked-engines=database.engine

To patch multiple objects at once, separate the paths with a whitespace:

.. code-block:: ini
    :caption: :file:`setup.cfg`

    [tool:pytest]
    mocked-engines=database.engine database.second_engine

.. _mocked-sessions:

``mocked-sessions``
~~~~~~~~~~~~~~~~~~~

The `mocked-sessions` property directs the plugin to `patch <https://docs.python.org/3/library/unittest.mock.html#unittest.mock.patch>`_ objects in your codebase,
typically SQLAlchemy `Session <http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine>`_ instances,
replacing them with the :ref:`db_session <db_session>` fixture such that any database updates performed by the objects get rolled back at the end of the test.

The value for this property should be formatted as a whitespace-separated list of standard Python import paths, like `database.db.session`. This property is **optional**.

Example:

.. code-block:: Python
    :caption: :file:`database.py`

    db = SQLAlchemy()

.. code-block:: ini
    :caption: :file:`setup.cfg`

    [tool:pytest]
    mocked-sessions=database.db.session

To patch multiple objects at once, separate the paths with a whitespace:

.. code-block:: ini
    :caption: :file:`setup.cfg`

    [tool:pytest]
    mocked-sessions=database.db.session database.second_db.session

.. _mocked-sessionmakers:

``mocked-sessionmakers``
~~~~~~~~~~~~~~~~~~~~~~~~

The `mocked-sessionmakers` property directs the plugin to `patch <https://docs.python.org/3/library/unittest.mock.html#unittest.mock.patch>`_ objects in your codebase,
typically instances of `SQLAlchemy's sessionmaker factory <http://docs.sqlalchemy.org/en/latest/orm/session_api.html?highlight=sessionmaker#sqlalchemy.orm.session.sessionmaker>`_,
replacing them with a mocked class that will return the transactional :ref:`db_session <db_session>` fixture.
This can be useful if you have pre-configured instances of sessionmaker objects that you import in the code to spin up sessions on the fly.

The value for this property should be formatted as a whitespace-separated list of standard Python import paths, like `database.WorkerSessionmaker`.
This property is **optional**.

.. rubric:: Example:

.. code-block:: Python
    :caption: :file:`database.py`

    WorkerSessionmaker = sessionmaker()


.. code-block:: ini
    :caption: :file:`setup.cfg`

    [tool:pytest]
    mocked-sessionmakers=database.WorkerSessionmaker

To patch multiple objects at once, separate the paths with a whitespace.

.. code-block:: ini
    :caption: :file:`setup.cfg`

    [tool:pytest]
    mocked-sessionmakers=database.WorkerSessionmaker database.SecondWorkerSessionmaker

Writing transactional tests
---------------------------

Once you have your :ref:`conftest file set up <conftest-setup>` and you've :ref:`overrided the necessary connectables in your test configuration <test-configuration>`, you're ready to write some transactional tests.
Simply import one of the module's :ref:`transactional fixtures <Fixtures>` in your test signature, and the test will be wrapped in a transaction.

Note that by default, **tests are only wrapped in transactions if they import one of the** :ref:`transactional fixtures <Fixtures>` **provided by this module.**
Tests that do not import the fixture will interact with your database without opening a transaction:

.. code-block:: Python

    # This test will be wrapped in a transaction.
    def transactional_test(db_session):
        ...

    # This test **will not** be wrapped in a transaction, since it does not import a
    # transactional fixture.
    def non_transactional_test():
        ...

The fixtures provide a way for you to control which tests require transactions and which don't.
This is often useful, since avoiding transaction setup can speed up tests that don't interact with your database.

For more information about the transactional fixtures provided by this module, read on to the :ref:`fixtures section <Fixtures>`.
For guidance on how to automatically enable transactions without having to specify fixtures,
see the section on :ref:`enabling transactions without fixtures <enabling-transactions-without-fixtures>`.
