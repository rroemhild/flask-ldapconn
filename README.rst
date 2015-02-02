Flask-LDAPConn
==============

Flask-LDAPConn is a Flask extension providing `python-ldap <http://www.python-ldap.org/>`_ connection object for accessing LDAP servers.


Installation
------------

.. code-block:: bash

    pip install flask-ldapconn


Configuration
-------------

Your configuration should be declared within your Flask config. Sample configuration:

.. code-block:: python

    LDAP_URI = 'ldap://localhost:389'
    LDAP_BINDDN = 'cn=admin,dc=example,dc=com'
    LDAP_SECRET = 'forty-two'
    LDAP_TIMEOUT = 10
    LDAP_USE_TLS = True
    LDAP_USE_SSL = False
    LDAP_REQUIRE_CERT = False
    LDAP_CERT_PATH = '/etc/openldap/certs'

To create the ldap instance within your application

.. code-block:: python

    from flask import Flask
    from flask_ldapconn import LDAPConn

    app = Flask(__name__)
    ldap_conn = LDAPConn(app)

or

.. code-block:: python

    from flask import Flask
    from flask_ldapconn import LDAPConn

    ldap_conn = LDAPConn()

    def create_app():
        app = Flask(__name__)
        ldap_conn.init_app(app)
        return app


Usage
-----

.. code-block:: python

    from ldap import SCOPE_SUBTREE
    from app import ldap_conn

    @app.route('/')
    def index():
        basedn = 'ou=people,dc=example,dc=com'
        searchfilter = '(objectClass=posixAccount)'
        attrs = ['sn', 'givenName', 'uid', 'mail']        
        result = ldap_conn.connection.search_s(basedn, SCOPE_SUBTREE,
                                               search_filter, attrs)


Contribute
----------

#. Check for open issues or open a fresh issue to start a discussion around a feature idea or a bug. There is a Contributor Friendly tag for issues that should be ideal for people who are not very familiar with the codebase yet.
#. Fork `the repository`_ on Github to start making your changes to the **master** branch (or branch off of it).
#. Write a test which shows that the bug was fixed or that the feature works as expected.
#. Send a pull request and bug the maintainer until it gets merged and published.

.. _`the repository`: http://github.com/rroemhild/flask-ldapconn

