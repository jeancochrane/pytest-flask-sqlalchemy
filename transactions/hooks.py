import pytest


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(items):
    '''
    Check if any tests are marked as transactional.
    '''
    for item in items:
        if item.get_marker('transactional'):
            item.fixturenames.append('db_session')

