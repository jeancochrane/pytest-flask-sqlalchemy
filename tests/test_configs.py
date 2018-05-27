def test_missing_db_connection_string(db_testdir):
    '''
    Test the case where the user has forgotten to specify a DB connection string
    when attempting to use the `module_engine` fixture.
    '''
    db_testdir.makepyfile("""
        def test_missing_db_connection_string(module_engine):
            # The fixture setup should fail, so don't worry about the test
            pass
    """)

    result = db_testdir.runpytest()
    result.assert_outcomes(error=1)
    result.stdout.fnmatch_lines([
        "*The configuration option 'db-connection-string' is required to use the `module_engine` fixture.*",
    ])


def test_malformed_db_connection_string(db_testdir):
    '''
    Test the case where a user has provided a DB connection string that does not
    produce a valid database connection when attempting to use the `module_engine`
    fixture.
    '''
    db_testdir.makeini("""
        [pytest]
        db-connection-string=blahblahblah
    """)

    db_testdir.makepyfile("""
        def test_missing_db_connection_string(module_engine):
            # The fixture setup should fail, so don't worry about the test
            pass
    """)

    result = db_testdir.runpytest()
    result.assert_outcomes(error=1)
    result.stdout.fnmatch_lines([
        "*SQLAlchemy could not parse a rfc1738 URL from the string*",
    ])


def test_mocked_engines(db_testdir):
    '''
    Test that we can specify paths to specific Engine objects that the plugin
    will mock.
    '''
    db_testdir.makeini("""
        [pytest]
        mocked_engines=collections.namedtuple collections.deque
    """)

    db_testdir.makepyfile("""

        def test_mocked_engines(db_engine):
            from collections import namedtuple, deque
            assert type(namedtuple) == 'Mock'
            assert type(deque) == 'Mock'
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
        mocked_sessions=collections.namedtuple collections.deque
    """)

    db_testdir.makepyfile("""

        def test_mocked_sessions(db_session):
            from collections import namedtuple, deque
            assert type(namedtuple) == 'Mock'
            assert type(deque) == 'Mock'
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
        mocked_sessionmakers=collections.namedtuple collections.deque
    """)

    db_testdir.makepyfile("""

        def test_mocked_sessionmakers(db_session):
            from collections import namedtuple, deque
            assert type(namedtuple) == 'Mock'
            assert type(deque) == 'Mock'
    """)

    result = db_testdir.runpytest()
    result.assert_outcomes(passed=1)
