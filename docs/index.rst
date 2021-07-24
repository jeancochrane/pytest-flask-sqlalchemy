.. PyTest-Flask-SQLAlchemy documentation master file, created by
   sphinx-quickstart on Fri Sep 20 10:22:51 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=======================
PyTest-Flask-SQLAlchemy
=======================

.. image:: https://badge.fury.io/py/pytest-flask-sqlalchemy.svg
    :target: https://badge.fury.io/py/pytest-flask-sqlalchemy

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   Quick Start     <quickstart>
   Install         <installation>
   Usage           <utilization>
   Fixtures        <fixtures>
   Databases       <databases>
   Design          <design>

A `pytest <https://docs.pytest.org/en/latest/>`_ plugin providing fixtures for running tests in transactions using `Flask-SQLAlchemy <http://flask-sqlalchemy.pocoo.org/latest/>`_.

Motivation
----------

Inspired by `Django's built-in support for transactional tests <https://jeancochrane.com/blog/django-test-transactions>`_, this plugin seeks to provide comprehensive, easy-to-use Pytest fixtures for wrapping tests in database transactions for `Flask-SQLAlchemy <http://flask-sqlalchemy.pocoo.org/latest/>`_ apps.
The goal is to make testing stateful Flask-SQLAlchemy applications easier by providing fixtures that permit the developer to **make arbitrary database updates with the confidence that any changes made during a test will roll back** once the test exits.

Acknowledgements
----------------

This plugin was initially developed for testing `Dedupe.io  <https://dedupe.io>`_, a web app for record linkage and entity resolution using machine learning.
Dedupe.io is built and maintained by `DataMade <https://datamade.us>`_.

The code is greatly indebted to `Alex Michael <https://github.com/alexmic>`_, whose blog post `"Delightful testing with pytest and Flask-SQLAlchemy" <http://alexmic.net/flask-sqlalchemy-pytest/>`_ helped establish the basic approach on which this plugin builds.

Many thanks to `Igor Ghisi <https://github.com/igortg/>`_, who donated the PyPi package name.
Igor had been working on a similar plugin and proposed combining efforts.
Thanks to Igor, the plugin name is much stronger.

Copyright
----------------

Copyright (c) 2019 Jean Cochrane and DataMade. Released under the MIT License.

Third-party copyright in this distribution is noted where applicable.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
