from .fixtures import _db, _transaction, _engine, _session, db_session, db_engine
from .hooks import pytest_collection_modifyitems

def pytest_addoption(parser):
    '''
    Add additional command-line args.
    '''
    base_msg = ('A whitespace-separated list of {obj} objects that should ' +
                'be mocked and replaced with a transactional equivalent. ' +
                'Each instance should be formatted as a standard ' +
                'Python import path. Useful for mocking global objects that are ' +
                "imported throughout your app's internal code.")

    parser.addini('mocked-engines',
                  type='args',
                  help=base_msg.format(obj='SQLAlchemy Engine'))

    parser.addini('mocked-sessions',
                  type='args',
                  help=base_msg.format(obj='SQLAlchemy Session'))

    parser.addini('mocked-sessionmakers',
                  type='args',
                  help=base_msg.format(obj='SQLAlchemy Sessionmaker'))


def pytest_configure(config):
    '''
    Add transactional options to pytest's configuration.
    '''
    config._mocked_engines = config.getini('mocked-engines')
    config._mocked_sessions = config.getini('mocked-sessions')
    config._mocked_sessionmakers = config.getini('mocked-sessionmakers')


def pytest_load_initial_conftests(early_config, parser, args):
    '''
    Register marks.
    '''
    early_config.addinivalue_line(
        'markers',
        'transactional: Mark the test to be run inside a nested transaction, with '
        'any database changes rolled back at the end of the test. Note that '
        "running tests in transactions requires you to configure the 'mocked-sessions', "
        "'mocked-engines', and 'mocked-sessionmakers' properties in your test "
        'config file so that any objects you are using to update the database are '
        'appropriately replaced with their transactional equivalent.')
