def test_use_db_session_to_alter_database(db_testdir):
    '''
    Test that creating objects and emitting SQL in the ORM won't bleed into
    other tests.
    '''
    # Load tests from file
    db_testdir.makepyfile("""
        def test_use_db_session_to_alter_database(person, db_engine, db_session):

            # Create a new object instance using the ORM
            opts = {
                'id': 1,
                'name': 'tester'
            }

            new_inst = person(**opts)

            db_session.add(new_inst)
            db_session.commit()

            # Create a new object instance by emitting raw SQL from the session object
            db_session.execute('''
                insert into person (id, name)
                values (2, 'second tester')
            ''')

            # Make sure that the session object has registered changes
            name_list = db_session.execute('''select name from person''').fetchall()
            names = [name[0] for name in name_list]

            assert 'tester' in names
            assert 'second tester' in names

        def test_db_session_changes_dont_persist(person, db_engine, db_session):

            assert not db_engine.execute('''select * from person''').fetchone()
            assert not db_session.query(person).first()
    """)

    # Run tests
    result = db_testdir.runpytest()
    result.assert_outcomes(passed=2)


def test_use_db_engine_to_alter_database(db_testdir):
    '''
    Use the `db_engine` fixture to alter the database directly.
    '''
    db_testdir.makepyfile("""
        def test_use_db_engine_to_alter_database(person, db_engine, db_session):

            db_engine.execute('''
                insert into person (id, name)
                values (1, 'tester')
            ''')

            # Use the contextmanager to retrieve a connection
            with db_engine.begin() as conn:
                conn.execute('''
                    insert into person (id, name)
                    values (2, 'second tester')
                ''')

            first_person = db_session.query(person).get(1)
            second_person = db_session.query(person).get(2)

            assert first_person.name == 'tester'
            assert second_person.name == 'second tester'

        def test_db_engine_changes_dont_persist(person, db_engine, db_session):

            assert not db_engine.execute('''select * from person''').fetchone()
            assert not db_session.query(person).first()
    """)

    result = db_testdir.runpytest()
    result.assert_outcomes(passed=2)


def test_raise_programmingerror_rolls_back_transaction(db_testdir):
    '''
    Make sure that when a ProgrammingError gets raised and handled, the
    connection will continue to be useable.
    '''
    db_testdir.makepyfile("""
        import pytest
        import sqlalchemy as sa

        def test_raise_programmingerror_rolls_back_transaction(person, db_engine, db_session):

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
                nonexistent_person = conn.execute('''SELECT name FROM person''').fetchone()

            assert not nonexistent_person

            # Make some changes that we can check in the following test
            db_engine.execute('''
                insert into person (id, name)
                values (1, 'tester')
            ''')

            person = db_session.query(person).get(1)
            assert person.name == 'tester'

        def test_raise_programmingerror_changes_dont_persist(person, db_engine, db_session):

            assert not db_engine.execute('''select * from person''').fetchone()
            assert not db_session.query(person).first()
    """)

    result = db_testdir.runpytest()
    result.assert_outcomes(passed=2)


def test_transaction_commit(db_testdir):
    '''
    Make some changes directly using the Transaction object and confirm that
    they appear.
    '''
    db_testdir.makepyfile("""
        def test_transaction_commit(person, db_engine, db_session):

            with db_engine.begin() as conn:
                trans = conn.begin()

                conn.execute('''
                    insert into person (id, name)
                    values (1, 'tester')
                ''')

                trans.commit()

                conn.close()

            person = db_session.query(person).get(1)
            assert person.name == 'tester'

        def test_transaction_commit_changes_dont_persist(person, db_engine, db_session):

            assert not db_engine.execute('''select * from person''').fetchone()
            assert not db_session.query(person).first()
    """)

    result = db_testdir.runpytest()
    result.assert_outcomes(passed=2)


def test_transaction_rollback(db_testdir):
    '''
    Attempt to roll back the active transaction and then alter the database. When not
    handled properly, this can have the effect of causing changes to persist
    across tests.
    '''
    db_testdir.makepyfile("""
        import sqlalchemy as sa

        def test_transaction_rollback(person, db_engine, db_session):

            db_engine.execute('''
                insert into person (id, name)
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

            person = db_session.query(person).get(1)
            assert person.name == 'tester'

        def test_transaction_rollback_changes_dont_persist(person, db_engine, db_session):

            assert not db_engine.execute('''select * from person''').fetchone()
            assert not db_session.query(person).first()
    """)

    result = db_testdir.runpytest()
    result.assert_outcomes(passed=2)


def test_drop_table(db_testdir):
    '''
    Make sure that we can drop tables and verify they do not exist in the context
    of a test.
    '''
    db_testdir.makepyfile("""
        def test_drop_table(person, db_engine):

            # Drop the raw table
            db_engine.execute('''
                DROP TABLE "person"
            ''')

            # Check if the raw table exists
            existing_tables = db_engine.execute('''
                SELECT relname
                FROM pg_catalog.pg_class
                WHERE relkind in ('r', 'm')
                AND relname = 'person'
            ''').first()

            assert not existing_tables

        def test_drop_table_changes_dont_persist(person, db_engine):

            existing_tables = db_engine.execute('''
                SELECT relname
                FROM pg_catalog.pg_class
                WHERE relkind in ('r', 'm')
                AND relname = 'person'
            ''').first()

            assert existing_tables
    """)

    result = db_testdir.runpytest()
    result.assert_outcomes(passed=2)


def test_use_raw_connection_to_alter_database(db_testdir):
    '''
    Retrieve a raw DBAPI connection and use it to make changes to the database.
    '''
    db_testdir.makepyfile("""
        def test_use_raw_connection_to_alter_database(person, db_engine, db_session):

            # Make some changes so that we can make sure they persist after a raw connection
            # rollback
            db_engine.execute('''
                insert into person (id, name)
                values (1, 'tester')
            ''')

            # Make changes with a raw connection
            conn = db_engine.raw_connection()
            cursor = conn.cursor()

            cursor.execute('''
                insert into person (id, name)
                values (2, 'second tester')
            ''')

            conn.commit()

            # Check to make sure that the changes are visible to the original connection
            second_person = db_engine.execute('''select name from person where id = 2''').fetchone()[0]

            assert second_person == 'second tester'

            # Roll back the changes made by the raw connection
            conn.rollback()
            conn.close()

            # Make sure earlier changes made by the original connection persist after rollback
            person = db_session.query(person).get(1)
            assert person.name == 'tester'


        def test_raw_connection_changes_dont_persist(person, db_engine, db_session):

            assert not db_engine.execute('''select * from person''').fetchone()
            assert not db_session.query(person).first()
    """)

    result = db_testdir.runpytest()
    result.assert_outcomes(passed=2)
