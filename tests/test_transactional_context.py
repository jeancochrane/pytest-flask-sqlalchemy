def test_loaded_files(testfile, conftest, testdir):
    '''
    Run all tests for this file using a temporary conftest file.
    '''
    # Load a temp conftest from file
    testdir.makeconftest(conftest)

    # Load tests from file
    testdir.makepyfile("""
        import pytest

        def test_pytester(table, db_session):
            '''
            Make sure pytester works.
            '''
            assert 1 + 1 == 2
    """)

    # Run tests
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
