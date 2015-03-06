Flask-LDAPConn
==============

.. image:: https://travis-ci.org/rroemhild/flask-ldapconn.png?branch=master
    :target: https://travis-ci.org/rroemhild/flask-ldapconn

.. image:: https://pypip.in/version/flask-ldapconn/badge.svg?style=flat
    :target: https://pypi.python.org/pypi/flask-ldapconn/
    :alt: Latest Version

.. image:: https://pypip.in/download/flask-ldapconn/badge.svg?style=flat
    :target: https://pypi.python.org/pypi/flask-ldapconn/
    :alt: Downloads

.. image:: https://pypip.in/py_versions/flask-ldapconn/badge.svg?style=flat
    :target: https://pypi.python.org/pypi/flask-ldapconn/
    :alt: Supported Python versions

.. image:: https://pypip.in/license/flask-ldapconn/badge.svg?style=flat
    :target: https://pypi.python.org/pypi/flask-ldapconn/
    :alt: License

Flask-LDAPConn is a Flask extension providing `ldap3 <https://github.com/cannatag/ldap3>`_ (an LDAP V3 pure Python client) connection for accessing LDAP servers.

To abstract access to LDAP data this extension also provides a simple model class, currently with read-only access, based on the `ldap3.abstract <http://ldap3.readthedocs.org/en/latest/abstraction.html>`_ package.


Installation
------------

.. code-block:: shell

    pip install flask-ldapconn


Configuration
-------------

Your configuration should be declared within your Flask config. Sample configuration:

.. code-block:: python

    from ssl import CERT_OPTIONAL

    LDAP_SERVER = 'localhost'
    LDAP_PORT = 389
    LDAP_BINDDN = 'cn=admin,dc=example,dc=com'
    LDAP_SECRET = 'forty-two'
    LDAP_TIMEOUT = 10
    LDAP_USE_TLS = True
    LDAP_REQUIRE_CERT = CERT_OPTIONAL
    LDAP_CERT_PATH = '/etc/openldap/certs'

Create the ldap instance within your application:

.. code-block:: python

    from flask import Flask
    from flask_ldapconn import LDAPConn

    app = Flask(__name__)
    ldap = LDAPConn(app)


Client sample
-------------

.. code-block:: python

    from flask import Flask
    from flask_ldapconn import LDAPConn
    from ldap3 import SUBTREE

    app = Flask(__name__)
    ldap = LDAPConn(app)

    @app.route('/')
    def index():
        ldapc = ldap.connection
        basedn = 'ou=people,dc=example,dc=com'
        search_filter = '(objectClass=posixAccount)'
        attributes = ['sn', 'givenName', 'uid', 'mail']
        ldapc.search(basedn, search_filter, SUBTREE,
                     attributes=attributes)
        response = ldapc.response


User model sample
-----------------

.. code-block:: python

    from flask import Flask
    from flask_ldapconn import LDAPConn

    app = Flask(__name__)
    ldap = LDAPConn(app)

    class User(ldap.BaseModel):

        __basedn__ = 'ou=people,dc=example,dc=com'
        __objectclass__ = ['inetOrgPerson']

        name = ldap.BaseAttr('cn')
        email = ldap.BaseAttr('mail')
        userid = ldap.BaseAttr('uid')

    with app.app_context():
        u = User()
        entries = u.search('email: @example.com')
        for entry in entries:
            print u'Name: {}'.format(entry.name)


Authentication sample
---------------------

.. code-block:: python

    from flask import Flask
    from flask_ldapconn import LDAPConn

    app = Flask(__name__)
    ldap = LDAPConn(app)

    username = 'user1'
    password = 'userpass'
    attribute = 'uid'
    search_filter = ('(active=1)')

    with app.app_context():
        retval = ldap.authenticate(username, password, attribute,
                                   basedn, search_filter')
        if not retval:
            return 'Invalid credentials.'
        return 'Welcome %s.' % username


Unit Test
---------

I use a simple Docker image to run the tests on localhost. The test file ``test_flask_ldapconn.py`` tries to handle ``start`` and ``stop`` of the docker container:

.. code-block:: shell

    pip install docker-py
    docker pull rroemhild/test-openldap
    python test_flask_ldapconn.py

Run the docker container manual:

.. code-block:: shell

    docker run --privileged -d -p 389:389 --name flask_ldapconn rroemhild/test-openldap
    DOCKER_RUN=False python test_flask_ldapconn.py

Unit test with your own settings from a file:

.. code-block:: shell

    LDAP_SETTINGS=my_settings.py python test_flask_ldapconn.py


Contribute
----------

#. Check for open issues or open a fresh issue to start a discussion around a feature idea or a bug.
#. Fork `the repository`_ on Github to start making your changes.
#. Write a test which shows that the bug was fixed or that the feature works as expected.
#. Send a pull request and bug the maintainer until it gets merged and published.

.. _`the repository`: http://github.com/rroemhild/flask-ldapconn
