import pytest
import sqlalchemy as sa


def test_use_db_session_to_alter_database(user, db_session):
    '''
    Test that creating objects and emitting SQL in the ORM won't bleed into
    other tests.
    '''
    # Create a new object instance using the ORM
    opts = {
        'id': 1,
        'name': 'tester'
    }

    new_inst = table(**opts)

    db_session.add(new_inst)
    db_session.commit()

    # Create a new object instance by emitting raw SQL from the session object
    db_session.execute('''
        insert into user (id, name)
        values (2, 'second tester')
    ''')

    # Make sure that the session object has registered changes
    name_list = db_session.execute('''select name from user''').fetchall()
    names = [name[0] for name in name_list]

    assert 'tester' in names
    assert 'second tester' in names


def test_db_session_changes_dont_persist(user, db_session):
    '''
    Test that the changes made in `test_use_db_session_to_alter_database` have not
    persisted.
    '''
    assert not db_engine.execute('''select * from user''').fetchone()[0]


def test_use_db_engine_to_alter_database(user, db_engine, db_session):
    '''
    Use the `db_engine` fixture to alter the database directly.
    '''
    db_engine.execute('''
        insert into user (id, name)
        values (1, 'tester')
    ''')

    # Use the contextmanager to retrieve a connection
    with db_engine.begin() as conn:
        conn.execute('''
            insert into user (id, name)
            values (2, 'second tester')
        ''')

    user = db_session.query(user).get(1)
    second_user = db_session.query(user).get(2)

    assert user.name == 'tester'
    assert second_user.name == 'second tester'


def test_db_engine_changes_dont_persist(user, db_engine, db_session):
    '''
    Make sure that changes made in `test_use_db_engine_in_test_to_alter_database`
    don't persist across tests.
    '''
    assert not db_engine.execute('''select * from user''').fetchone()[0]
    assert not db_session.query(user).first()


def test_raise_programmingerror_rolls_back_transaction(user, db_engine, db_session):
    '''
    Make sure that when a ProgrammingError gets raised and handled, the
    connection will continue to be useable.
    '''
    # Confirm that we can raise a ProgrammingError
    with pytest.raises(sa.exc.ProgrammingError):
        # Run a query that doesn't correspond to an existing table
        with db_engine.begin() as conn:
            db_engine.execute('''
                SELECT record_count FROM 'browser'
            ''')

    # Handle the ProgrammingError the way we do in the code (try/except block)
    try:
        with db_engine.begin() as conn:
            conn.execute('''
                SELECT record_count FROM 'browser'
            ''')
    except sa.exc.ProgrammingError:
        pass

    # This query will raise an InternalError if ProgrammingErrors don't get handled properly,
    # since the ProgrammingError aborts the transaction by default
    with db_engine.begin() as conn:
        nonexistent_user = conn.execute('''SELECT name FROM user''').fetchone()[0]

    assert not nonexistent_user

    # Make some changes that we can check in the following test
    db_engine.execute('''
        insert into user (id, name)
        values (1, 'tester')
    ''')

    user = db_session.query(user).get(1)
    assert user.name == 'tester'


def test_raise_programmingerror_changes_dont_persist(dataset_id, db_engine, db_session):
    '''
    Make sure that when a ProgrammingError gets raised and handled, the changes
    made don't persist across tests.
    '''
    assert not db_engine.execute('''select * from user''').fetchone()[0]
    assert not db_session.query(user).first()


def test_transaction_commit(user, db_engine, db_session):
    '''
    Make some changes directly using the Transaction object and confirm that
    they appear.
    '''
    with db_engine.begin() as conn:
        trans = conn.begin()

        conn.execute('''
            insert into user (id, name)
            values (1, 'tester')
        ''')

        trans.commit()

        conn.close()

    user = db_session.query(user).get(1)
    assert user.name == 'tester'


def test_transaction_commit_changes_dont_persist(user, db_engine, db_session):
    '''
    Make sure that changes made in `test_transaction_commit`
    don't persist across tests.
    '''
    assert not db_engine.execute('''select * from user''').fetchone()[0]
    assert not db_session.query(user).first()


def test_transaction_rollback(dataset_id, db_engine, db_session):
    '''
    Attempt to roll back the active transaction and then alter the database. When not
    handled properly, this can have the effect of causing changes to persist
    across tests.
    '''
    db_engine.execute('''
        insert into user (id, name)
        values (1, 'tester')
    ''')

    with db_engine.begin() as conn:
        trans = conn.begin()

        try:
            conn.execute('''
                SELECT record_count FROM 'browser'
            ''')
        except sa.exc.ProgrammingError:
            trans.rollback()

        conn.close()

    user = db_session.query(user).get(1)
    assert user.name == 'tester'


def test_transaction_rollback_changes_dont_persist(user, db_engine, db_session):
    '''
    Make sure that changes made in `test_transaction_rollback`
    don't persist across tests.
    '''
    assert not db_engine.execute('''select * from user''').fetchone()[0]
    assert not db_session.query(user).first()


def test_drop_table(user, db_engine):
    '''
    Make sure that we can drop tables and verify they do not exist in the context
    of a test.
    '''
    # Drop the raw table
    db_engine.execute('''
        DROP TABLE "user"
    ''')

    # Check if the raw table exists
    existing_tables = db_engine.execute('''
        SELECT relname
        FROM pg_catalog.pg_class
        WHERE relkind in ('r', 'm')
          AND relname = 'user'
    ''').first()

    assert not existing_tables


def test_drop_table_changes_dont_persist(user, db_engine):
    '''
    Make sure changes made in `test_drop_table_during_test` do not persist across
    tests.
    '''
    existing_tables = db_engine.execute('''
        SELECT relname
        FROM pg_catalog.pg_class
        WHERE relkind in ('r', 'm')
          AND relname = 'user'
    ''').first()

    assert existing_tables


def test_use_raw_connection_to_alter_database(user, db_engine, db_session):
    '''
    Retrieve a raw DBAPI connection and use it to make changes to the database.
    '''
    # Make some changes so that we can make sure they persist after a raw connection
    # rollback
    db_engine.execute('''
        insert into user (id, name)
        values (1, 'tester')
    ''')

    # Make changes with a raw connection
    conn = db_engine.raw_connection()
    cursor = conn.cursor()

    cursor.execute('''
        insert into user (id, name)
        values (2, 'second tester')
    ''')

    conn.commit()

    # Check to make sure that the changes are visible to the original connection
    second_user = db_engine.execute('''select name from user where id = 2''').fetchone()[0]

    assert second_user.name == 'second tester'

    # Roll back the changes made by the raw connection
    conn.rollback()
    conn.close()

    # Make sure earlier changes made by the original connection persist after rollback
    user = db_session.query(user).get(1)
    assert user.name == 'tester'


def test_raw_connection_changes_dont_persist(dataset_id, db_engine, db_session):
    '''
    Make sure changes made in `test_use_raw_connection_in_test_to_alter_database`
    do not persist across tests.
    '''
    assert not db_engine.execute('''select * from user''').fetchone()[0]
    assert not db_session.query(user).first()
