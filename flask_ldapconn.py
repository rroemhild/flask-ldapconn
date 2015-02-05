# -*- coding: utf-8 -*-

from ssl import CERT_REQUIRED, CERT_OPTIONAL, PROTOCOL_TLSv1
from ldap3 import Server, Connection, Tls
from ldap3 import AUTH_SIMPLE, STRATEGY_SYNC, GET_ALL_INFO, SUBTREE
from ldap3 import AUTO_BIND_TLS_BEFORE_BIND, ALL_ATTRIBUTES, DEREF_ALWAYS

from flask import current_app


__all__ = ['LDAPConn']


try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


class LDAPConn(object):

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):

        # Default config
        app.config.setdefault('LDAP_URI', 'ldap://localhost:389')
        app.config.setdefault('LDAP_SERVER', 'localhost')
        app.config.setdefault('LDAP_PORT', 389)
        app.config.setdefault('LDAP_BINDDN', None)
        app.config.setdefault('LDAP_SECRET', None)
        app.config.setdefault('LDAP_TIMEOUT', 10)
        app.config.setdefault('LDAP_USE_TLS', True)
        app.config.setdefault('LDAP_REQUIRE_CERT', CERT_OPTIONAL)
        app.config.setdefault('LDAP_CERT_PATH', None)

        self.tls = Tls(validate=app.config['LDAP_REQUIRE_CERT'],
                  version=PROTOCOL_TLSv1,
                  ca_certs_file=app.config['LDAP_CERT_PATH'])

        self.ldap_server = Server(
            host=app.config['LDAP_SERVER'],
            port=app.config['LDAP_PORT'],
            get_info=GET_ALL_INFO
        )

    def connect(self):
        ldap_conn = Connection(
            self.ldap_server,
            auto_bind=AUTO_BIND_TLS_BEFORE_BIND,
            client_strategy=STRATEGY_SYNC,
            user=current_app.config['LDAP_BINDDN'],
            password=current_app.config['LDAP_SECRET'],
            authentication=AUTH_SIMPLE,
            check_names=True
        )

        #ldap_conn.bind()

        if current_app.config['LDAP_USE_TLS']:
            ldap_conn.tls = self.tls
            ldap_conn.start_tls()

        return ldap_conn

    def teardown(self, exception):
        ctx = stack.top
        if hasattr(ctx, 'ldap_conn'):
            ctx.ldap_conn.unbind()

    @property
    def connection(self):
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'ldap_conn'):
                ctx.ldap_conn = self.connect()
            return ctx.ldap_conn

    def get_result(self):
        return self.connection.result

    def get_response(self):
        return self.connection.response

    def search(self, *args, **kwargs):
        return self.connection.search(*args, **kwargs)

    def whoami(self):
        return self.connection.extend.standard.who_am_i()

