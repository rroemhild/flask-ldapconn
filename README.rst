Flask-LDAPConn
==============

.. image:: https://travis-ci.org/rroemhild/flask-ldapconn.svg?branch=master
    :target: https://travis-ci.org/rroemhild/flask-ldapconn

.. image:: https://badge.fury.io/py/flask-ldapconn.svg
    :target: https://pypi.python.org/pypi/flask-ldapconn

Flask-LDAPConn is a Flask extension providing `ldap3 <https://github.com/cannatag/ldap3>`_ (an LDAP V3 pure Python client) connection for accessing LDAP servers.

To abstract access to LDAP data this extension provides a simple ORM model.


Installation
------------

.. code-block:: shell

    pip install flask-ldapconn


Configuration
-------------

Your configuration should be declared within your Flask config. Sample configuration:

.. code-block:: python

    import ssl

    LDAP_SERVER = 'localhost'
    LDAP_PORT = 389
    LDAP_BINDDN = 'cn=admin,dc=example,dc=com'
    LDAP_SECRET = 'forty-two'
    LDAP_TIMEOUT = 10
    LDAP_USE_TLS = True  # default
    LDAP_REQUIRE_CERT = ssl.CERT_NONE  # default: CERT_REQUIRED
    LDAP_TLS_VERSION = ssl.PROTOCOL_TLSv1_2  # default: PROTOCOL_TLSv1
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


User model samples
------------------

.. code-block:: python

    from flask import Flask
    from flask_ldapconn import LDAPConn

    app = Flask(__name__)
    ldap = LDAPConn(app)

    class User(ldap.Entry):

        base_dn = 'ou=people,dc=example,dc=com'
        object_classes = ['inetOrgPerson']

        name = ldap.Attribute('cn')
        email = ldap.Attribute('mail')
        userid = ldap.Attribute('uid')
        surname = ldap.Attribute('sn')
        givenname = ldap.Attribute('givenName')

    with app.app_context():

        # get a list of entries
        entries = User.query.filter('email: *@example.com').all()
        for entry in entries:
            print u'Name: {}'.format(entry.name)

        # get the first entry
        user = User.query.filter('userid: user1').first()

        # new entry
        new_user = User(
            name='User Three',
            email='user3@example.com',
            userid='user3',
            surname='Three',
            givenname='User'
        )
        new_user.save()

        # modify entry
        mod_user = User.query.filter('userid: user1').first()
        mod_user.name = 'User Number Three'
        mod_user.email.append.('u.three@example.com')
        mod_user.givenname.delete()
        mod_user.save()

        # remove entry
        rm_user = User.query.filter('userid: user1').first()
        rm_user.delete()

        # authenticate user
        auth_user = User.query.filter('userid: user1').first()
        if auth_user:
            if auth_user.authenticate('password1234'):
                print('Authenticated')
            else:
                print('Wrong password')


Authenticate with Client
------------------------

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


Bind as user
------------

To bind as user for the current request save a new connection to ``flask.g.ldap_conn``:

.. code-block:: python

    g.ldap_conn = ldap.connect(userdn, password)
    user = User.query.get(userdn)

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
