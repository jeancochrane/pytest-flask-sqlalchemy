def test_mark_rolls_back_db_updates(db_testdir):
    '''
    Test that the mark can successfully roll back any database transactions
    triggered by a test.
    '''
    db_testdir.makeini("""
        [pytest]
        mocked-sessions=test_mark_rolls_back_db_updates0.database.db.session
    """)

    db_testdir.makepyfile(__init__='')

    db_testdir.makepyfile(database="""
        import flask_sqlalchemy

        db = flask_sqlalchemy.SQLAlchemy()
    """)

    db_testdir.makepyfile("""
        from .database import db
        import pytest

        @pytest.mark.transactional
        def test_mark_rolls_back_db_updates(person):
            new_inst = person(id=1, name='tester')
            db.session.add(new_inst)
            db.session.commit()
            assert db.session.query(person).first().name == 'tester'

        @pytest.mark.transactional
        def test_mark_changes_dont_persist(person):
            assert not db.session.query(person).first()
    """)

    result = db_testdir.runpytest()
    result.assert_outcomes(passed=2)
