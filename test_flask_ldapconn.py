#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import time
import unittest

import flask

from ldap3 import SUBTREE
from flask_ldapconn import LDAPConn
from flask_ldapconn.compat import print_function, to_bytes


DOCKER_RUN = os.environ.get('DOCKER_RUN', True)
DOCKER_URL = 'unix://var/run/docker.sock'

TESTING = True
USER_EMAIL = 'fry@planetexpress.com'
USER_PASSWORD = 'fry'
LDAP_SERVER = 'localhost'
LDAP_BINDDN = 'cn=admin,dc=planetexpress,dc=com'
LDAP_SECRET = 'GoodNewsEveryone'
LDAP_BASEDN = 'dc=planetexpress,dc=com'
LDAP_SEARCH_ATTR = 'mail'
LDAP_SEARCH_FILTER = '(mail=%s)' % USER_EMAIL
LDAP_QUERY_FILTER = 'email: %s' % USER_EMAIL
LDAP_OBJECTCLASS = ['inetOrgPerson']


LDAP_AUTH_BASEDN = 'ou=people,dc=planetexpress,dc=com'
LDAP_AUTH_ATTR = 'mail'
LDAP_AUTH_SEARCH_FILTER = '(objectClass=inetOrgPerson)'


class LDAPConnTestCase(unittest.TestCase):

    def setUp(self):
        app = flask.Flask(__name__)
        app.config.from_object(__name__)
        app.config.from_envvar('LDAP_SETTINGS', silent=True)
        ldap = LDAPConn(app)

        self.app = app
        self.ldap = ldap


class LDAPConnSearchTestCase(LDAPConnTestCase):

    def test_connection_search(self):
        attr = self.app.config['LDAP_SEARCH_ATTR']
        with self.app.test_request_context():
            ldapc = self.ldap.connection
            ldapc.search(self.app.config['LDAP_BASEDN'],
                         self.app.config['LDAP_SEARCH_FILTER'],
                         SUBTREE, attributes=[attr])
            result = ldapc.result
            response = ldapc.response
            self.assertTrue(response)
            self.assertEqual(response[0]['attributes'][attr][0],
                             self.app.config['USER_EMAIL'])

    def test_whoami(self):
        with self.app.test_request_context():
            conn = self.ldap.connection
            self.assertEqual(conn.extend.standard.who_am_i(),
                             to_bytes('dn:' + self.app.config['LDAP_BINDDN']))


class LDAPConnModelTestCase(unittest.TestCase):

    def setUp(self):
        app = flask.Flask(__name__)
        app.config.from_object(__name__)
        app.config.from_envvar('LDAP_SETTINGS', silent=True)
        ldap = LDAPConn(app)

        self.app = app
        self.ldap = ldap

        class User(self.ldap.Model):
            # LDAP meta-data
            base_dn = self.app.config['LDAP_BASEDN']
            object_classes = self.app.config['LDAP_OBJECTCLASS']

            # inetOrgPerson
            name = self.ldap.Attribute('cn')
            email = self.ldap.Attribute('mail')
            userid = self.ldap.Attribute('uid')

        self.user = User

    def test_model_search(self):
        with self.app.test_request_context():
            entries = self.user.search(
                'email: %s' % self.app.config['USER_EMAIL']
            )
            for entry in entries:
                self.assertEqual(entry.email.value,
                                 self.app.config['USER_EMAIL'])

    def test_model_search_set_attribute(self):
        new_email = 'philip@planetexpress.com'
        with self.app.test_request_context():
            entries = self.user.search(
                'email: %s' % self.app.config['USER_EMAIL']
            )
            entry = entries[0]
            entry.email = new_email
            self.assertEqual(entry.email.value, new_email)

    def test_model_search_set_attribute_list(self):
        new_email_list = ['philip@planetexpress.com',
                          'a.fry@planetexpress.com']
        with self.app.test_request_context():
            entries = self.user.search(
                'email: %s' % self.app.config['USER_EMAIL']
            )
            entry = entries[0]
            entry.email = new_email_list
            self.assertEqual(entry.email.value, new_email_list)

    def test_model_search_set_readonly_attr(self):
        with self.app.test_request_context():
            with self.assertRaises(Exception) as context:
                entries = self.user.search(
                    'email: %s' % self.app.config['USER_EMAIL']
                    )
                entry = entries[0]
                entry.email.key = 'readonly'
            self.assertTrue('attribute is read only' in context.exception)

    def test_model_new(self):
        with self.app.test_request_context():
            user = self.user()
            user.name = 'Rafael'
            user.email = 'rafael@planetexpress.com'
            self.assertEqual(user.email.value, 'rafael@planetexpress.com')


class LDAPConnAuthTestCase(LDAPConnTestCase):

    def test_authenticate_user(self):
        with self.app.test_request_context():
            retval = self.ldap.authenticate(
                username=self.app.config['USER_EMAIL'],
                password=self.app.config['USER_PASSWORD'],
                basedn=self.app.config['LDAP_AUTH_BASEDN'],
                attribute=self.app.config['LDAP_SEARCH_ATTR'],
            )
            self.assertTrue(retval)

    def test_authenticate_user_basedn_filter(self):
        with self.app.test_request_context():
            retval = self.ldap.authenticate(
                username=self.app.config['USER_EMAIL'],
                password=self.app.config['USER_PASSWORD'],
                attribute=self.app.config['LDAP_SEARCH_ATTR'],
                basedn=self.app.config['LDAP_AUTH_BASEDN'],
                search_filter=self.app.config['LDAP_AUTH_SEARCH_FILTER']
            )
            self.assertTrue(retval)

    def test_authenticate_user_invalid_credentials(self):
        with self.app.test_request_context():
            retval = self.ldap.authenticate(
                username=self.app.config['USER_EMAIL'],
                password='testpass',
                attribute=self.app.config['LDAP_SEARCH_ATTR'],
                basedn=self.app.config['LDAP_AUTH_BASEDN'],
            )
            self.assertFalse(retval)

    def test_authenticate_user_invalid_search_filter(self):
        with self.app.test_request_context():
            retval = self.ldap.authenticate(
                username=self.app.config['USER_EMAIL'],
                password=self.app.config['USER_PASSWORD'],
                attribute=self.app.config['LDAP_SEARCH_ATTR'],
                basedn=self.app.config['LDAP_AUTH_BASEDN'],
                search_filter='x=y'
            )
            self.assertFalse(retval)

    def test_authenticate_user_search_filter_no_result(self):
        with self.app.test_request_context():
            retval = self.ldap.authenticate(
                username=self.app.config['USER_EMAIL'],
                password=self.app.config['USER_PASSWORD'],
                attribute=self.app.config['LDAP_SEARCH_ATTR'],
                basedn=self.app.config['LDAP_AUTH_BASEDN'],
                search_filter='(uidNumber=*)'
            )
            self.assertFalse(retval)


class LDAPConnSSLTestCase(unittest.TestCase):

    def setUp(self):
        app = flask.Flask(__name__)
        app.config.from_object(__name__)
        app.config.from_envvar('LDAP_SETTINGS', silent=True)
        app.config['LDAP_PORT'] = app.config.get('LDAP_SSL_PORT', 636)
        app.config['LDAP_USE_SSL'] = True
        ldap = LDAPConn(app)

        self.app = app
        self.ldap = ldap

    def test_whoami(self):
        with self.app.test_request_context():
            conn = self.ldap.connection
            self.assertEqual(conn.extend.standard.who_am_i(),
                             to_bytes('dn:' + self.app.config['LDAP_BINDDN']))


class LDAPConnAnonymousTestCase(unittest.TestCase):

    def setUp(self):
        app = flask.Flask(__name__)
        app.config.from_object(__name__)
        app.config.from_envvar('LDAP_SETTINGS', silent=True)
        app.config['LDAP_BINDDN'] = None
        app.config['LDAP_SECRET'] = None
        ldap = LDAPConn(app)

        self.app = app
        self.ldap = ldap

    def test_whoami(self):
        with self.app.test_request_context():
            conn = self.ldap.connection
            self.assertEqual(conn.extend.standard.who_am_i(), None)


class LDAPConnNoTLSAnonymousTestCase(unittest.TestCase):

    def setUp(self):
        app = flask.Flask(__name__)
        app.config.from_object(__name__)
        app.config.from_envvar('LDAP_SETTINGS', silent=True)
        app.config['LDAP_BINDDN'] = None
        app.config['LDAP_SECRET'] = None
        app.config['LDAP_USE_TLS'] = False
        ldap = LDAPConn(app)

        self.app = app
        self.ldap = ldap

    def test_whoami(self):
        with self.app.test_request_context():
            conn = self.ldap.connection
            self.assertEqual(conn.extend.standard.who_am_i(), None)


class LDAPConnDeprecatedTestCAse(LDAPConnTestCase):

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
                             self.app.config['USER_EMAIL'])

    def test_whoami_dep_deprecated(self):
        with self.app.test_request_context():
            self.assertEqual(self.ldap.whoami(),
                             to_bytes('dn:' + self.app.config['LDAP_BINDDN']))


if __name__ == '__main__':
    success = False
    try:
        if DOCKER_RUN is not True:
            raise ValueError('Do not use docker')

        from docker import Client
        cli = Client(base_url=DOCKER_URL)
        container = cli.create_container(image='rroemhild/test-openldap',
                                         ports=[389, 636])

        print('Starting docker container {0}...'.format(container.get('Id')))
        cli.start(container, privileged=True, port_bindings={389: 389,
                                                             636: 636})

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
