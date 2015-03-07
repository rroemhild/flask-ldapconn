# -*- coding: utf-8 -*-

from ssl import CERT_OPTIONAL, PROTOCOL_TLSv1
from ldap3 import Server, Connection, Tls
from ldap3 import AttrDef, ObjectDef, Reader
from ldap3 import LDAPBindError, LDAPInvalidFilterError
from ldap3 import STRATEGY_SYNC, GET_ALL_INFO, SUBTREE
from ldap3 import AUTO_BIND_NO_TLS, AUTO_BIND_TLS_BEFORE_BIND

from flask import current_app
from flask import _app_ctx_stack as stack

__all__ = ('LDAPConn',)


class LDAPBaseModel(ObjectDef):

    __basedn__ = None
    __objectclass__ = ['top']

    def __init__(self):
        super(LDAPBaseModel, self).__init__(self.__objectclass__)
        self._build_attrdef()

    def _build_attrdef(self):
        for attr in dir(self):
            value = getattr(self, attr)
            if not isinstance(value, LDAPBaseAttr):
                continue
            attribute = AttrDef(value['name'], attr)
            self.add(attribute)

    def search(self, query):
        app = current_app._get_current_object()
        ldapc = app.extensions.get('ldap_conn').connection
        model_reader = Reader(ldapc, self, query, self.__basedn__)
        model_reader.search()
        return model_reader.entries


class LDAPBaseAttr(object):
    def __init__(self,
                 name,
                 validate=None,
                 pre_query=None,
                 post_query=None,
                 default=None,
                 dereference_dn=None):
        self.name = name
        self.validate = validate
        self.pre_query = pre_query
        self.post_query = post_query
        self.default = default
        self.dereference_dn = dereference_dn

    def __getitem__(self, attr):
        return self.__dict__[attr]


class LDAPConn(object):

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

        self.BaseModel = LDAPBaseModel
        self.BaseAttr = LDAPBaseAttr

    def init_app(self, app):
        # Default config
        app.config.setdefault('LDAP_SERVER', 'localhost')
        app.config.setdefault('LDAP_PORT', 389)
        app.config.setdefault('LDAP_BINDDN', None)
        app.config.setdefault('LDAP_SECRET', None)
        app.config.setdefault('LDAP_TIMEOUT', 10)
        app.config.setdefault('LDAP_USE_SSL', False)
        app.config.setdefault('LDAP_USE_TLS', True)
        app.config.setdefault('LDAP_REQUIRE_CERT', CERT_OPTIONAL)
        app.config.setdefault('LDAP_CERT_PATH', None)

        self.tls = Tls(validate=app.config['LDAP_REQUIRE_CERT'],
                       version=PROTOCOL_TLSv1,
                       ca_certs_file=app.config['LDAP_CERT_PATH'])

        self.ldap_server = Server(
            host=app.config['LDAP_SERVER'],
            port=app.config['LDAP_PORT'],
            use_ssl=app.config['LDAP_USE_SSL'],
            get_info=GET_ALL_INFO
        )

        # Store ldap_conn object to extensions
        app.extensions['ldap_conn'] = self

        # Teardown appcontext
        app.teardown_appcontext(self.teardown)

    def connect(self, user, password):
        auto_bind_strategy = AUTO_BIND_TLS_BEFORE_BIND
        if current_app.config['LDAP_USE_TLS'] is not True:
            auto_bind_strategy = AUTO_BIND_NO_TLS

        ldap_conn = Connection(
            self.ldap_server,
            auto_bind=auto_bind_strategy,
            client_strategy=STRATEGY_SYNC,
            user=user,
            password=password,
            check_names=True
        )

        return ldap_conn

    def teardown(self, exception):
        ctx = stack.top
        if hasattr(ctx, 'ldap_conn'):
            ctx.ldap_conn.unbind()

    @property
    def connection(self):
        user = current_app.config['LDAP_BINDDN']
        password = current_app.config['LDAP_SECRET']

        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'ldap_conn'):
                ctx.ldap_conn = self.connect(user, password)
            return ctx.ldap_conn

    def authenticate(self,
                     username,
                     password,
                     attribute,
                     basedn,
                     search_filter=None,
                     search_scope=SUBTREE):
        '''Attempts to bind a user to the LDAP server.

            :param username: The username to attempt to bind with.
            :param password: The password of the username.
            :param attribute: The LDAP attribute for the username.
            :param basedn: The LDAP basedn to search on.
            :param search_filter: LDAP searchfilter to attempt to search with.

            :return: ``True`` if successful or ``False`` if the
                credentials are invalid.
        '''
        user_filter = '({0}={1})'.format(attribute, username)
        if search_filter is not None:
            search_filter = '(&{0}{1})'.format(user_filter, search_filter)
        else:
            search_filter = user_filter

        try:
            self.connection.search(basedn, search_filter, search_scope,
                                   attributes=[attribute])
            response = self.connection.response
            conn = self.connect(response[0]['dn'], password)
            conn.unbind()
            return True
        except (LDAPBindError, LDAPInvalidFilterError, IndexError):
            return False

    def whoami(self):
        '''Deprecated

        Use LDAPConn.connection.extend.standard.who_am_i()
        '''
        return self.connection.extend.standard.who_am_i()

    def result(self):
        '''Deprecated

        Use LDAPConn.connection.result
        '''
        return self.connection.result

    def response(self):
        '''Deprecated

        Use LDAPConn.connection.response
        '''
        return self.connection.response

    def search(self, *args, **kwargs):
        '''Deprecated

        Use LDAPConn.connection.search()
        '''
        return self.connection.search(*args, **kwargs)
