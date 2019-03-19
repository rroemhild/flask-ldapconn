#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import ssl
import json
import time
import random
import string
import unittest
import flask

from ldap3 import SUBTREE, STRING_TYPES
from ldap3.core.exceptions import LDAPAttributeError, LDAPStartTLSError

from flask_ldapconn import LDAPConn

from flask_ldapconn.entry import LDAPEntry
from flask_ldapconn.attribute import LdapField


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
LDAP_TLS_VERSION = ssl.PROTOCOL_TLSv1
LDAP_REQUIRE_CERT = ssl.CERT_NONE

LDAP_AUTH_BASEDN = 'ou=people,dc=planetexpress,dc=com'
LDAP_AUTH_ATTR = 'mail'
LDAP_AUTH_SEARCH_FILTER = '(objectClass=inetOrgPerson)'

UID_SUFFIX = ''.join(random.choice(
    string.ascii_lowercase + string.digits
) for _ in range(6))


def is_json(myjson):
    try:
        json.loads(myjson)
    except (ValueError, TypeError):
        return False
    return True


class User(LDAPEntry):
    # LDAP meta-data
    base_dn = LDAP_AUTH_BASEDN
    entry_rdn = ['cn', 'uid']
    object_classes = ['inetOrgPerson']

    # inetOrgPerson
    name = LdapField('cn')
    email = LdapField('mail')
    title = LdapField('title')
    userid = LdapField('uid')
    surname = LdapField('sn')
    givenname = LdapField('givenName')


class Account(User):
    # LDAP meta-data
    object_classes = ['posixAccount']

    # posixAccount
    uidnumber = LdapField('uidNumber')
    gidnumber = LdapField('gidNumber')
    shell = LdapField('loginShell')
    home = LdapField('homeDirectory')
    password = LdapField('userPassword')


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
                             'dn:{}'.format(self.app.config['LDAP_BINDDN']))


class LDAPConnModelTestCase(unittest.TestCase):

    def setUp(self):
        app = flask.Flask(__name__)
        app.config.from_object(__name__)
        app.config.from_envvar('LDAP_SETTINGS', silent=True)
        ldap = LDAPConn(app)

        self.app = app
        self.ldap = ldap
        self.user = User

    def test_model_search(self):
        with self.app.test_request_context():
            entry = self.user.query.filter(
                'email: %s' % self.app.config['USER_EMAIL']
            ).first()
            self.assertEqual(entry.email,
                             self.app.config['USER_EMAIL'])

    def test_model_search_set_attribute(self):
        new_email = 'philip@planetexpress.com'
        with self.app.test_request_context():
            entry = self.user.query.filter(
                'email: %s' % self.app.config['USER_EMAIL']
            ).first()
            entry.email = new_email
            self.assertEqual(entry.email, new_email)

    def test_model_search_set_attribute_list(self):
        new_email_list = ['philip@planetexpress.com',
                          'a.fry@planetexpress.com']
        with self.app.test_request_context():
            entry = self.user.query.filter(
                'email: %s' % self.app.config['USER_EMAIL']
            ).first()
            entry.email = new_email_list
            self.assertEqual(entry.email, new_email_list)

    def test_model_search_set_undefined_attr(self):
        def new_model():
            user = self.user(active='1')
        with self.app.test_request_context():
            self.assertRaises(LDAPAttributeError, new_model)

    def test_model_new(self):
        with self.app.test_request_context():
            user = self.user(name='Rafael Römhild',
                             email='rafael@planetexpress.com')
            self.assertEqual(user.email, 'rafael@planetexpress.com')

    def test_model_fetch_entry(self):
        uid = 'bender'
        with self.app.test_request_context():
            user = self.user.query.filter('userid: {}'.format(uid)).first()
            self.assertEqual(user.userid, uid)

    def test_model_fetch_entry_with_components_in_and_false(self):
        uid = 'bender'
        with self.app.test_request_context():
            user = self.user.query.filter(
                'email: {0}, userid: {0}'.format(uid)
            ).all(components_in_and=False)
            self.assertEqual(user[0].userid, uid)

    def test_model_fetch_entry_authenticate(self):
        uid = 'fry'
        with self.app.test_request_context():
            user = self.user.query.filter('userid: {}'.format(uid)).first()
            password = self.app.config['USER_PASSWORD']
            self.assertTrue(user.authenticate(password))

    def test_model_fetch_entry_exception(self):
        uid = 'xyz'
        with self.app.test_request_context():
            user = self.user.query.filter('userid: {}'.format(uid)).first()
            self.assertEqual(user, None)

    def test_model_fetch_multible_entries(self):
        expected_uids = ['bender', 'fry', 'hermes', 'leela', 'professor',
                         'zoidberg']
        response_uids = []
        query_filter = 'email: *@planetexpress.com'
        with self.app.test_request_context():
            entries = self.user.query.filter(query_filter).all()
            for entry in entries:
                response_uids.append(entry.userid)
        matched_uids = set(expected_uids).intersection(response_uids)
        self.assertEqual(len(expected_uids), len(matched_uids))

    def test_model_get_dn(self):
        dn = 'cn=Philip J. Fry,ou=people,dc=planetexpress,dc=com'
        with self.app.test_request_context():
            user = self.user.query.get(dn)
            self.assertEqual(dn, user.dn)

    def test_model_get_multivalued_rdn(self):
        dn = 'cn=Amy Wong+sn=Kroker,ou=people,dc=planetexpress,dc=com'
        with self.app.test_request_context():
            user = self.user.query.get(dn)
            self.assertEqual('Kroker', user.surname)

    def test_model_get_attributes_dict(self):
        with self.app.test_request_context():
            user = self.user.query.filter('userid: bender').first()
            attrs = ['name', 'email', 'userid']
            attr_dict = user.get_attributes_dict()
            self.assertTrue(isinstance(attr_dict, dict))
            for attr in attrs:
                self.assertTrue(isinstance(attr_dict[attr], list))

    def test_model_to_json(self):
        with self.app.test_request_context():
            user = self.user.query.filter('userid: bender').first()
            self.assertTrue(is_json(user.to_json()))

    def test_model_to_json_str_values(self):
        with self.app.test_request_context():
            user = self.user.query.filter('userid: bender').first()
            self.assertTrue(is_json(user.to_json(str_values=True)))

    def test_model_iter(self):
        with self.app.test_request_context():
            user = self.user.query.filter('userid: bender').first()
            for name, field in user._fields.items():
                self.assertTrue(isinstance(field, self.ldap.Attribute))

    def test_model_contains(self):
        with self.app.test_request_context():
            user = self.user.query.filter('userid: bender').first()
            self.assertTrue(hasattr(user, 'userid'))

    def test_model_getarr_att_not_found(self):
        with self.app.test_request_context():
            user = self.user.query.filter('userid: bender').first()
            self.assertFalse(hasattr(user, 'active'))

    def test_model_setattr(self):
        with self.app.test_request_context():
            user = self.user.query.filter('userid: fry').first()
            user.userid = 'xyz'
            self.assertEqual(user.userid, 'xyz')

    def test_model_attribute_str(self):
        with self.app.test_request_context():
            user = self.user.query.filter('userid: fry').first()
            self.assertTrue(isinstance(user.userid, STRING_TYPES))

    def test_model_attribute_value_force_list(self):
        with self.app.test_request_context():
            self.app.config['FORCE_ATTRIBUTE_VALUE_AS_LIST'] = True
            user = self.user.query.filter('userid: fry').first()
            self.assertTrue(isinstance(user.userid, list))

    def test_model_attribute_iter(self):
        with self.app.test_request_context():
            user = self.user.query.filter('userid: professor').first()
            self.assertTrue(isinstance(user.email, list))
            for mail in user.email:
                pass

    def test_model_operation_add(self):
        uid = 'rafael-{}'.format(UID_SUFFIX)
        query_filter = 'userid: {}'.format(uid)
        with self.app.test_request_context():
            new_user = self.user(name='Rafael Römhild',
                                 userid=uid,
                                 email='rafael@planetexpress.com',
                                 surname='Römhild',
                                 givenname='Raphael')
            self.assertTrue(new_user.save())
            user = self.user.query.filter(query_filter).first()
            self.assertEqual(new_user.userid, user.userid)

    def test_model_operation_modify(self):
        uid = 'rafael-{}'.format(UID_SUFFIX)
        query_filter = 'userid: {}'.format(uid)
        with self.app.test_request_context():
            mod_user = self.user.query.filter(query_filter).first()
            mod_user.givenname = 'Rafael'
            mod_user.title = 'SysAdmin'
            mod_user.email = [mod_user.email, 'it@planetexpress.co']
            self.assertTrue(mod_user.save())
            user = self.user.query.filter(query_filter).first()
            self.assertEqual(user.givenname, 'Rafael')
            self.assertEqual(user.surname, u'Römhild')
            self.assertEqual(user.title, 'SysAdmin')
            self.assertTrue('it@planetexpress.co' in user.email)

    def test_model_operation_remove(self):
        uid = 'rafael-{}'.format(UID_SUFFIX)
        query_filter = 'userid: {}'.format(uid)
        with self.app.test_request_context():
            user = self.user.query.filter(query_filter).first()
            self.assertTrue(user.delete())
            user = self.user.query.filter(query_filter).first()
            self.assertEqual(user, None)


class LDAPConnModelInheritanceTestCase(unittest.TestCase):

    def setUp(self):
        app = flask.Flask(__name__)
        app.config.from_object(__name__)
        app.config.from_envvar('LDAP_SETTINGS', silent=True)
        ldap = LDAPConn(app)

        self.app = app
        self.ldap = ldap
        self.user = Account

    def test_model_operation_add(self):
        uid = 'rafael-{}'.format(UID_SUFFIX)
        query_filter = 'userid: {}'.format(uid)
        with self.app.test_request_context():
            new_user = self.user(name='Rafael Römhild',
                                 userid=uid,
                                 email='rafael@planetexpress.com',
                                 surname='Römhild',
                                 givenname='Raphael',
                                 uidnumber=1000,
                                 gidnumber=1000,
                                 shell='/bin/false',
                                 home='/home/' + uid)
            self.assertTrue(new_user.save())
            user = self.user.query.filter(query_filter).first()
            self.assertEqual(new_user.userid, user.userid)

    def test_model_operation_modify(self):
        uid = 'rafael-{}'.format(UID_SUFFIX)
        query_filter = 'userid: {}'.format(uid)
        with self.app.test_request_context():
            mod_user = self.user.query.filter(query_filter).first()
            mod_user.givenname = 'Rafael'
            mod_user.title = 'SysAdmin'
            mod_user.shell = '/bin/bash'
            mod_user.email = [mod_user.email, 'it@planetexpress.co']
            self.assertTrue(mod_user.save())
            user = self.user.query.filter(query_filter).first()
            self.assertEqual(user.givenname, 'Rafael')
            self.assertEqual(user.surname, u'Römhild')
            self.assertEqual(user.title, 'SysAdmin')
            self.assertTrue('it@planetexpress.co' in user.email)

    def test_model_operation_remove(self):
        uid = 'rafael-{}'.format(UID_SUFFIX)
        query_filter = 'userid: {}'.format(uid)
        with self.app.test_request_context():
            user = self.user.query.filter(query_filter).first()
            self.assertTrue(user.delete())
            user = self.user.query.filter(query_filter).first()
            self.assertEqual(user, None)


class LDAPConnAuthTestCase(LDAPConnTestCase):

    def test_authenticate_user(self):
        with self.app.test_request_context():
            retval = self.ldap.authenticate(
                username=self.app.config['USER_EMAIL'],
                password=self.app.config['USER_PASSWORD'],
                base_dn=self.app.config['LDAP_AUTH_BASEDN'],
                attribute=self.app.config['LDAP_SEARCH_ATTR'],
            )
            self.assertTrue(retval)

    def test_authenticate_user_with_dn(self):
        dn = 'cn=Philip J. Fry,ou=people,dc=planetexpress,dc=com'
        with self.app.test_request_context():
            retval = self.ldap.authenticate(
                username=dn,
                password=self.app.config['USER_PASSWORD'],
            )
            self.assertTrue(retval)

    def test_authenticate_user_basedn_filter(self):
        with self.app.test_request_context():
            retval = self.ldap.authenticate(
                username=self.app.config['USER_EMAIL'],
                password=self.app.config['USER_PASSWORD'],
                attribute=self.app.config['LDAP_SEARCH_ATTR'],
                base_dn=self.app.config['LDAP_AUTH_BASEDN'],
                search_filter=self.app.config['LDAP_AUTH_SEARCH_FILTER']
            )
            self.assertTrue(retval)

    def test_authenticate_user_invalid_credentials(self):
        with self.app.test_request_context():
            retval = self.ldap.authenticate(
                username=self.app.config['USER_EMAIL'],
                password='testpass',
                attribute=self.app.config['LDAP_SEARCH_ATTR'],
                base_dn=self.app.config['LDAP_AUTH_BASEDN'],
            )
            self.assertFalse(retval)

    def test_authenticate_user_invalid_search_filter(self):
        with self.app.test_request_context():
            retval = self.ldap.authenticate(
                username=self.app.config['USER_EMAIL'],
                password=self.app.config['USER_PASSWORD'],
                attribute=self.app.config['LDAP_SEARCH_ATTR'],
                base_dn=self.app.config['LDAP_AUTH_BASEDN'],
                search_filter='x=y'
            )
            self.assertFalse(retval)

    def test_authenticate_user_search_filter_no_result(self):
        with self.app.test_request_context():
            retval = self.ldap.authenticate(
                username=self.app.config['USER_EMAIL'],
                password=self.app.config['USER_PASSWORD'],
                attribute=self.app.config['LDAP_SEARCH_ATTR'],
                base_dn=self.app.config['LDAP_AUTH_BASEDN'],
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
                             'dn:{}'.format(self.app.config['LDAP_BINDDN']))


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


class LDAPConnTLSCertRequiredTestCase(unittest.TestCase):
    def setUp(self):
        app = flask.Flask(__name__)
        app.config.from_object(__name__)
        app.config.from_envvar('LDAP_SETTINGS', silent=True)
        app.config['LDAP_BINDDN'] = None
        app.config['LDAP_SECRET'] = None
        app.config['LDAP_REQUIRE_CERT'] = ssl.CERT_REQUIRED
        ldap = LDAPConn(app)

        self.app = app
        self.ldap = ldap

    def connect(self):
        return self.ldap.connection

    def test_connection(self):
        with self.app.test_request_context():
            self.assertRaises(LDAPStartTLSError, self.connect)


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


class LDAPConnDeprecatedTestCase(LDAPConnTestCase):

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

    def test_whoami_deprecated(self):
        with self.app.test_request_context():
            whoami = self.ldap.whoami()
            self.assertEqual(whoami,
                             'dn:{}'.format(self.app.config['LDAP_BINDDN']))


if __name__ == '__main__':
    success = False
    try:
        import docker
        client = docker.from_env()
        container = client.containers.run('rroemhild/test-openldap',
                                          ports={'389/tcp': 389,
                                                 '636/tcp': 636},
                                          detach=True,
                                          privileged=True,
                                          remove=True)

        print('Docker container {0} started'.format(container.id))
        print('Wait 3 seconds until slapd is started...')
        time.sleep(3)

        print('Run unit test...')
        runner = unittest.main(exit=False)
        success = runner.result.wasSuccessful()

        print('Stop and removing container...')
        container.stop()
    except (ImportError, ValueError):
        print('Can\'t run docker image. Try to run tests without.')
        unittest.main()

    if success is not True:
        sys.exit(1)
