from .fixtures import _transaction, _engine, _session, db_session, db_engine, module_engine


def pytest_addoption(parser):
    '''
    Add additional command-line args.
    '''
    parser.addini('db-connection-string',
                  help='A connection string specifiying the path to your test database.')

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
    config._dbconn = config.getini('db-connection-string')
    config._mocked_engines = config.getini('mocked-engines')
    config._mocked_sessions = config.getini('mocked-sessions')
    config._mocked_sessionmakers = config.getini('mocked-sessionmakers')
