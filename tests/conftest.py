import os

import pytest

# This import prevents SQLAlchemy from throwing an AttributeError
# claiming that <class 'object'> is already a registered type -- it is suspicious
# code and should eventually be either confirmed to fix a bug, or removed
from flask_sqlalchemy import SQLAlchemy

pytest_plugins = ['pytester']


@pytest.fixture(scope='module')
def conftest():
    '''
    Load configuration file for the tests to a string, in order to run it in
    its own temporary directory.
    '''
    with open(os.path.join('tests', '_conftest.py'), 'r') as conf:
        conftest = conf.read()

    return conftest


@pytest.fixture
def db_testdir(conftest, testdir):
    '''
    Set up a temporary test directory loaded with the configuration file for
    the tests.
    '''
    testdir.makeconftest(conftest)

    return testdir
