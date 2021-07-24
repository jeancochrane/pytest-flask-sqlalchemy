------
Design
------

Development
===========

Running the tests
-----------------

To run the tests, start by installing a development version of the plugin that includes test dependencies:

.. code-block:: console

    pip install -e .[tests]


Next, export a `database connection string <http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls>`_ that the tests can use (the database referenced by the string will be created during test setup, so it does not need to exist):

.. code-block:: console

    export TEST_DATABASE_URL=<db_connection_string>

Finally, run the tests using pytest:

.. code-block:: console

    pytest
