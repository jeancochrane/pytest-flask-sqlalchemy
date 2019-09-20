--------------
Quick examples
--------------

Use the :ref:`db_session fixture <db_session>` to make **database updates that won't persist beyond the body of the test**::

    def test_a_transaction(db_session):
       row = db_session.query(Table).get(1)
       row.name = 'testing'

       db_session.add(row)
       db_session.commit()

    def test_transaction_doesnt_persist(db_session):
       row = db_session.query(Table).get(1)
       assert row.name != 'testing'

The :ref:`db_engine fixture <db_engine>` works the same way, but **copies the API of SQLAlchemy's** `Engine object <http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine>`_::

    def test_a_transaction_using_engine(db_engine):
        with db_engine.begin() as conn:
            row = conn.execute('''UPDATE table SET name = 'testing' WHERE id = 1''')

    def test_transaction_doesnt_persist(db_engine):
        row_name = db_engine.execute('''SELECT name FROM table WHERE id = 1''').fetchone()[0]
        assert row_name != 'testing'

Use :ref:`configuration properties <test-configuration>` to **mock database connections in an app and enforce nested transactions**, allowing any method from the codebase to run inside a test with the assurance that any database changes made will be rolled back at the end of the test:

.. code-block:: ini
    :caption: :file:`setup.cfg`
    :name: configuration

    [tool:pytest]
    mocked-sessions=database.db.session
    mocked-engines=database.engine


.. code-block:: python
    :caption: :file:`database.py`
    :name: database

    db = flask_sqlalchemy.SQLAlchemy()
    engine = sqlalchemy.create_engine('DATABASE_URI')


.. code-block:: python
    :caption: :file:`models.py`
    :name: models

    class Table(db.Model):
        __tablename__ = 'table'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(80))

        def set_name(new_name)
            self.name = new_name
            db.session.add(self)
            db.session.commit()


.. code-block:: python
    :caption: :file:`tests/test_set_name.py`
    :name: test:set name

    def test_set_name(db_session):
        row = db_session.query(Table).get(1)
        row.set_name('testing')
        assert row.name == 'testing'

    def test_transaction_doesnt_persist(db_session):
       row = db_session.query(Table).get(1)
       assert row.name != 'testing'

