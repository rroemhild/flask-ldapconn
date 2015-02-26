#!/usr/bin/env python
# -*- coding: utf-8 -*-
from compat import print_function, to_bytes

import os
import sys
import time
import unittest

import flask
import flask_ldapconn

from ldap3 import SUBTREE
from flask_ldapconn import LDAPConn


DOCKER_RUN = os.environ.get('DOCKER_RUN', True)
DOCKER_URL = 'unix://var/run/docker.sock'

TESTING = True
EMAIL = 'fry@planetexpress.com'
LDAP_SERVER = 'localhost'
LDAP_BINDDN = 'cn=admin,dc=planetexpress,dc=com'
LDAP_SECRET = 'GoodNewsEveryone'
LDAP_BASEDN = 'ou=people,dc=planetexpress,dc=com'
LDAP_SEARCH_ATTR = 'mail'
LDAP_SEARCH_FILTER = '(mail=%s)' % EMAIL
LDAP_QUERY_FILTER = 'email: %s' % EMAIL
LDAP_OBJECTCLASS = ['inetOrgPerson']


class LDAPConnTestCase(unittest.TestCase):

    def setUp(self):
        app = flask.Flask(__name__)
        app.config.from_object(__name__)
        app.config.from_envvar('LDAP_SETTINGS', silent=True)
        ldap = flask_ldapconn.LDAPConn(app)

        self.app = app
        self.ldap = ldap

    def test_connection_search(self):
        attr = self.app.config['LDAP_SEARCH_ATTR']
        with self.app.test_request_context():
            self.ldap.search(self.app.config['LDAP_BASEDN'],
                             self.app.config['LDAP_SEARCH_FILTER'],
                             SUBTREE, attributes=[attr])
            result = self.ldap.result()
            response = self.ldap.response()
            self.assertTrue(response)
            self.assertEqual(response[0]['attributes'][attr][0],
                             self.app.config['EMAIL'])

    def test_model_search(self):
        class User(self.ldap.BaseModel):

            __basedn__ = self.app.config['LDAP_BASEDN']
            __objectclass__ = self.app.config['LDAP_OBJECTCLASS']

            name = self.ldap.BaseAttr('cn')
            userid = self.ldap.BaseAttr('uid')
            email = self.ldap.BaseAttr('mail')

        with self.app.test_request_context():
            u = User()
            entries = u.search('email: %s' % self.app.config['EMAIL'])
            for entry in entries:
                self.assertEqual(entry.email.value,
                                 self.app.config['EMAIL'])

    def test_whoami(self):
        with self.app.test_request_context():
            self.assertEqual(self.ldap.whoami(),
                             to_bytes('dn:' + self.app.config['LDAP_BINDDN']))


class LDAPConnAnonymousTestCase(LDAPConnTestCase):

    def setUp(self):
        app = flask.Flask(__name__)
        app.config.from_object(__name__)
        app.config.from_envvar('LDAP_SETTINGS', silent=True)
        app.config['LDAP_BINDDN'] = None
        app.config['LDAP_SECRET'] = None
        ldap = flask_ldapconn.LDAPConn(app)

        self.app = app
        self.ldap = ldap

    def test_whoami(self):
        with self.app.test_request_context():
            self.assertEqual(self.ldap.whoami(), None)


class LDAPConnNoTLSAnonymousTestCase(unittest.TestCase):

    def setUp(self):
        app = flask.Flask(__name__)
        app.config.from_object(__name__)
        app.config.from_envvar('LDAP_SETTINGS', silent=True)
        app.config['LDAP_BINDDN'] = None
        app.config['LDAP_SECRET'] = None
        app.config['LDAP_USE_TLS'] = False
        ldap = flask_ldapconn.LDAPConn(app)

        self.app = app
        self.ldap = ldap

    def test_whoami(self):
        with self.app.test_request_context():
            self.assertEqual(self.ldap.whoami(), None)


if __name__ == '__main__':
    success = False
    try:
        if DOCKER_RUN is not True:
            raise ValueError('Do not use docker')

        from docker import Client
        cli = Client(base_url=DOCKER_URL)
        container = cli.create_container(image='rroemhild/test-openldap',
                                         ports=[389])

        print('Starting docker container {0}...'.format(container.get('Id')))
        cli.start(container, privileged=True, port_bindings={389: 389})

        print('Wait 3 seconds until slapd is started...')
        time.sleep(3)

        print('Run unit test...')
        runner = unittest.main(exit=False)
        success = runner.result.wasSuccessful()

        print('Stop and removing container...')
        cli.remove_container(container, force=True)
    except (ImportError, ValueError):
        unittest.main()

    if success is not True:
        sys.exit(1)
