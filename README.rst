Flask-LDAPConn
==============

Flask-LDAPConn is a Flask extension providing `ldap3 <https://github.com/cannatag/ldap3>`_ (an LDAP V3 pure Python client) connection for accessing LDAP servers.

To abstract access to LDAP data this extension also provides a simple model class, currently with read-only access, based on the `ldap3.abstract <http://ldap3.readthedocs.org/en/latest/abstraction.html>`_ package.


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

To create the ldap instance within your application:

.. code-block:: python

    from flask import Flask
    from flask_ldapconn import LDAPConn

    app = Flask(__name__)
    ldap_conn = LDAPConn(app)


Client sample
-------------

.. code-block:: python

    from flask import Flask
    from flask_ldapconn import LDAPConn
    from ldap3 import SUBTREE

    app = Flask(__name__)
    ldap_conn = LDAPConn(app)

    @app.route('/')
    def index():
        basedn = 'ou=people,dc=example,dc=com'
        search_filter = '(objectClass=posixAccount)'
        attributes = ['sn', 'givenName', 'uid', 'mail']
        ldap_conn.search(basedn, search_filter, SUBTREE,
                         attributes=attributes)
        response = ldap_conn.get_response()


User model sample
-----------------

.. code-block:: python

    from flask import Flask
    from flask_ldapconn import LDAPConn

    app = Flask(__name__)
    ldap_conn = LDAPConn(app)

    class User(ldap_conn.BaseModel):

        __basedn__ = 'ou=people,dc=example,dc=com'
        __objectclass__ = ['inetOrgPerson']

        name = ldap_conn.BaseAttr('cn')
        email = ldap_conn.BaseAttr('mail')
        userid = ldap_conn.BaseAttr('uid')

    with app.app_context():
        u = User()
        entries = u.search('email: @example.com')
        for entry in entries:
            print u'Name: {}'.format(entry.name)


Contribute
----------

#. Check for open issues or open a fresh issue to start a discussion around a feature idea or a bug. There is a Contributor Friendly tag for issues that should be ideal for people who are not very familiar with the codebase yet.
#. Fork `the repository`_ on Github to start making your changes to the **master** branch (or branch off of it).
#. Write a test which shows that the bug was fixed or that the feature works as expected.
#. Send a pull request and bug the maintainer until it gets merged and published.

.. _`the repository`: http://github.com/rroemhild/flask-ldapconn

