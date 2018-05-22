'''
pytest-flask-sqlalchemy-transactions
====================================

Run tests in transactions using pytest, Flask, and SQLAlchemy.
'''
import os
from setuptools import setup

with open(os.path.join('requirements', 'main.txt')) as reqfile:
    requirements = reqfile.read().splitlines()

setup(
    # Metadata
    name='pytest-flask-sqlalchemy-transactions',
    author='Jean Cochrane',
    author_email='jean@jeancochrane.com',

    url='https://github.com/jeancochrane/pytest-flask-sqlalchemy-transactions',
    description='Run tests in transactions using pytest, Flask, and SQLalchemy.',
    long_description=__doc__,
    license='MIT',

    packages=['transactions'],
    install_requires=requirements,

    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Plugins',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Framework :: Pytest',
    ],

    # Make the package available to pytest
    entry_points={
        'pytest11': [
            'pytest-flask-sqlalchemy-transactions = transactions.plugin',
        ]
    },
)
