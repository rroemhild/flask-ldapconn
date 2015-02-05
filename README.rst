Flask-LDAPConn
==============

Flask-LDAPConn is a Flask extension providing `ldap3 <https://github.com/cannatag/ldap3>`_ (an LDAP V3 pure Python client) connection object for accessing LDAP servers.


Installation
------------

.. code-block:: bash

    pip install flask-ldapconn


Configuration
-------------

Your configuration should be declared within your Flask config. Sample configuration:

.. code-block:: python

    LDAP_SERVER = 'localhost'
    LDAP_PORT = 389
    LDAP_BINDDN = 'cn=admin,dc=example,dc=com'
    LDAP_SECRET = 'forty-two'
    LDAP_TIMEOUT = 10
    LDAP_USE_TLS = True
    LDAP_CERT_PATH = '/etc/openldap/certs'

To create the ldap instance within your application

.. code-block:: python

    from flask import Flask
    from flask_ldapconn import LDAPConn

    app = Flask(__name__)
    ldap_conn = LDAPConn(app)


Usage
-----

.. code-block:: python

    from ldap3 import SUBTREE
    from app import ldap_conn

    @app.route('/')
    def index():
        basedn = 'ou=people,dc=example,dc=com'
        search_filter = '(objectClass=posixAccount)'
        attributes = ['sn', 'givenName', 'uid', 'mail']
        ldap_conn.search(basedn, search_filter, SUBTREE,
                         attributes=attributes)
        response = ldap_conn.get_response()


Contribute
----------

#. Check for open issues or open a fresh issue to start a discussion around a feature idea or a bug. There is a Contributor Friendly tag for issues that should be ideal for people who are not very familiar with the codebase yet.
#. Fork `the repository`_ on Github to start making your changes to the **master** branch (or branch off of it).
#. Write a test which shows that the bug was fixed or that the feature works as expected.
#. Send a pull request and bug the maintainer until it gets merged and published.

.. _`the repository`: http://github.com/rroemhild/flask-ldapconn

