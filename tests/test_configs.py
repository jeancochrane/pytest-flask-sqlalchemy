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
            assert str(namedtuple).startswith("<transactions.fixtures._session.<locals>.FakeSessionMaker")
            assert str(Counter).startswith("<transactions.fixtures._session.<locals>.FakeSessionMaker")
    """)

    result = db_testdir.runpytest()
    result.assert_outcomes(passed=1)
