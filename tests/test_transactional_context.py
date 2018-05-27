def test_use_db_session_to_alter_database(orm_testfile, db_testdir):
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

def test_use_db_engine_to_alter_database(orm_testfile, db_testdir):
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
