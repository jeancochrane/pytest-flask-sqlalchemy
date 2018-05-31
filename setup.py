'''
pytest-flask-sqlalchemy-transactions
====================================

Run tests in transactions using pytest, Flask, and SQLAlchemy.
'''
from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()

setup(
    # Metadata
    name='pytest-flask-sqlalchemy-transactions',
    author='Jean Cochrane',
    author_email='jean@jeancochrane.com',

    url='https://github.com/jeancochrane/pytest-flask-sqlalchemy-transactions',
    description='Run tests in transactions using pytest, Flask, and SQLalchemy.',
    long_description=readme(),
    license='MIT',

    packages=['transactions'],
    install_requires=['pytest>=3.2.1',
                      'pytest-mock>=1.6.2',
                      'SQLAlchemy>=1.2.2',
                      'Flask-SQLAlchemy>=2.3'],
    extras_require={'tests': ['pytest-postgresql']},
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
