# -*- coding: utf-8 -*-

import ldap
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
        app.config.setdefault('LDAP_BINDDN', '')
        app.config.setdefault('LDAP_SECRET', '')
        app.config.setdefault('LDAP_TIMEOUT', 10)
        app.config.setdefault('LDAP_USE_TLS', True)
        app.config.setdefault('LDAP_USE_SSL', False)
        app.config.setdefault('LDAP_REQUIRE_CERT', False)
        app.config.setdefault('LDAP_CERT_PATH', '')

        ldap.set_option(ldap.OPT_PROTOCOL_VERSION, ldap.VERSION3)
        ldap.set_option(ldap.OPT_REFERRALS, ldap.DEREF_ALWAYS)
        ldap.set_option(ldap.OPT_DEREF, ldap.DEREF_ALWAYS)

        if app.config.get('LDAP_USE_SSL') or app.config.get('LDAP_USE_TLS'):
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_ALLOW)

        if app.config.get('LDAP_REQUIRE_CERT'):
            ldap.set_option(ldap.OPT_X_TLS_DEMAND, True)
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)
            ldap.set_option(ldap.OPT_X_TLS_CACERTFILE,
                            app.config.get('LDAP_CERT_PATH'))

    def connect(self):
        ldap_conn = ldap.initialize(current_app.config.get('LDAP_URI'))
        ldap_conn.set_option(ldap.OPT_NETWORK_TIMEOUT,
                             current_app.config.get('LDAP_TIMEOUT'))

        if current_app.config.get('LDAP_USE_TLS'):
            ldap_conn.start_tls_s()

        ldap_conn.simple_bind_s(current_app.config.get('LDAP_BINDDN'),
                                current_app.config.get('LDAP_SECRET'))
      
        return ldap_conn

    def teardown(self, exception):
        ctx = stack.top
        if hasattr(ctx, 'ldap_conn'):
            ctx.ldap_conn.unbind_s()

    @property
    def connection(self):
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'ldap_conn'):
                ctx.ldap_conn = self.connect()
            return ctx.ldap_conn

