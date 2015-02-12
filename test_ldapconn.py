# -*- coding: utf-8 -*-
from __future__ import with_statement

import unittest

import flask
import flask_ldapconn

from ldap3 import SUBTREE
from flask_ldapconn import LDAPConn


TESTING = True
EMAIL = 'user1@example.com'
LDAP_SERVER = 'localhost'
LDAP_BINDDN = 'cn=admin,dc=example,dc=com'
LDAP_SECRET = 's3cr3t'
LDAP_BASEDN = 'ou=people,dc=example,dc=com'
LDAP_SEARCH_ATTR = 'mail'
LDAP_SEARCH_FILTER = '(mail=%s)' % EMAIL
LDAP_QUERY_FILTER = 'email: %s' % EMAIL
LDAP_OBJECTCLASS = ['inetOrgPerson']


class LDAPConnTestCase(unittest.TestCase):

    def setUp(self):
        app = flask.Flask(__name__)
        app.config.from_object(__name__)
        app.config.from_object('config')
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
                             'dn:' + self.app.config['LDAP_BINDDN'])


if __name__ == '__main__':
    unittest.main()

