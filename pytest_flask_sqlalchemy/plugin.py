from .fixtures import _db, _transaction, _engine, _session, db_session, db_engine


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

    parser.addini('mocked-sessions-handle-connect-exceptions',
                  type='bool',
                  default=False,
                  help='Handle connection-time exceptions; engine and ' +
                       'session fixtures will contain empty (None) values ' +
                       'if SQLAlchemy could not establish a db connection')


def pytest_configure(config):
    '''
    Add transactional options to pytest's configuration.
    '''
    config._mocked_engines = config.getini('mocked-engines')
    config._mocked_sessions = config.getini('mocked-sessions')
    config._mocked_sessionmakers = config.getini('mocked-sessionmakers')
    config._handle_connect_failures = config.getini('mocked-sessions-handle-connect-exceptions')
