--------
Fixtures
--------

This plugin provides two fixtures for performing database updates inside nested transactions that get rolled back at the end of a test: :ref:`db_session <db_session>` and :ref:`db_engine <db_engine>`.
The fixtures provide similar functionality, but with different APIs.

.. _db_session:

``db_session``
==============

The :ref:`db_session <db_session>` fixture allows you to perform direct updates that will be rolled back when the test exits.
It exposes the same API as `SQLAlchemy's scoped_session object <http://docs.sqlalchemy.org/en/latest/orm/contextual.html#sqlalchemy.orm.scoping.scoped_session>`_.

Including this fixture as a function argument of a test will activate any mocks that are defined by the configuration properties :ref:`mocked-engines <mocked-engines>`, :ref:`mocked-sessions <mocked-sessions>`, or :ref:`mocked-sessionmakers <mocked-sessionmakers>` in the test configuration file for the duration of that test.

.. rubric:: Example:

.. code-block:: Python

    def test_a_transaction(db_session):
       row = db_session.query(Table).get(1)
       row.name = 'testing'

       db_session.add(row)
       db_session.commit()

    def test_transaction_doesnt_persist(db_session):
       row = db_session.query(Table).get(1)
       assert row.name != 'testing'


.. _db_engine:

``db_engine``
=============

Like :ref:`db_session <db_session>`, the `db_engine` fixture allows you to perform direct updates against the test database that will be rolled back when the test exits.
It is an instance of Python's built-in `MagicMock <https://docs.python.org/3/library/unittest.mock.html#unittest.mock.MagicMock>`_ class, with a spec set to match the API of `SQLAlchemy's Engine <http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine>`_ object.

Only a few `Engine` methods are exposed on this fixture:

- `db_engine.begin`: begin a new nested transaction (`API docs <http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine.begin>`_)
- `db_engine.execute`: execute a raw SQL query (`API docs <http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine.execute>`_)
- `db_engine.raw_connection`: return a raw DBAPI connection (`API docs <http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine.raw_connection>`_)

Since `db_engine` is an instance of `MagicMock` with an `Engine` spec, other methods of the `Engine` API can be called, but they will not perform any useful work.

Including this fixture as a function argument of a test will activate any mocks that are defined by the configuration properties :ref:`mocked-engines <mocked-engines>`, :ref:`mocked-sessions <mocked-sessions>`, or :ref:`mocked-sessionmakers <mocked-sessionmakers>` in the test configuration file for the duration of that test.

.. rubric:: Example:

.. code-block:: Python

    def test_a_transaction_using_engine(db_engine):
        with db_engine.begin() as conn:
            row = conn.execute('''UPDATE table SET name = 'testing' WHERE id = 1''')

    def test_transaction_doesnt_persist(db_engine):
        row_name = db_engine.execute('''SELECT name FROM table WHERE id = 1''').fetchone()[0]
        assert row_name != 'testing'

.. _enabling-transactions-without-fixtures:

Enabling transactions without fixtures
--------------------------------------

If you know you want to make all of your tests transactional, it can be annoying to have to specify one of the :ref:`fixtures <Fixtures>` in every test signature.

The best way to automatically enable transactions without having to include an extra fixture in every test is to wire up an `autouse fixture <https://docs.pytest.org/en/latest/fixture.html#autouse-fixtures-xunit-setup-on-steroids>`_ for your test suite.
This can be as simple as ::

    # Automatically enable transactions for all tests, without importing any extra fixtures.
    @pytest.fixture(autouse=True)
    def enable_transactional_tests(db_session):
        pass


In this configuration, the `enable_transactional_tests` fixture will be automatically used in all tests, meaning that `db_session` will also be used.
This way, all tests will be wrapped in transactions without having to explicitly require either `db_session` or `enable_transactional_tests`.

