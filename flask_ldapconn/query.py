# -*- coding: utf-8 -*-
from flask import current_app
from ldap3 import BASE, Reader


__all__ = ('BaseQuery',)


class BaseQuery(object):

    def __init__(self, type):
        self.type = type

        self.query = []
        self.base_dn = getattr(type, 'base_dn')
        self.sub_tree = getattr(type, 'sub_tree')
        self.object_def = getattr(type, '_object_def')
        self.components_in_and = True
        self.operational_attributes = getattr(type, 'operational_attributes')

    def __iter__(self):
        for entry in self.get_reader_result():
            new_cls = self.type.get_new_type()
            ldapentry = new_cls(dn=entry.entry_dn,
                                changetype='modify',
                                **entry.entry_attributes_as_dict)
            yield ldapentry

    def get_reader_result(self):
        query = ','.join(self.query)
        ldapc = current_app.extensions.get('ldap_conn')
        reader = Reader(connection=ldapc.connection,
                        object_def=self.object_def,
                        query=query,
                        base=self.base_dn,
                        components_in_and=self.components_in_and,
                        sub_tree=self.sub_tree,
                        get_operational_attributes=self.operational_attributes,
                        controls=None)
        reader.search()
        return reader.entries

    def get(self, ldap_dn):
        '''Return an LDAP entry by DN

        Args:
            ldap_dn (str): LDAP DN
        '''
        self.base_dn = ldap_dn
        self.sub_tree = BASE
        return self.first()

    def filter(self, *query_filter):
        '''Set the query filter to perform the query with

        Args:
            *query_filter: Simplified Query Language filter
        '''
        for query in query_filter:
            self.query.append(query)
        return self

    def first(self):
        '''Execute the query and return the first result

        If there are no entries, first returns ``None``
        '''
        for entry in iter(self):
            return entry
        return None

    def all(self, components_in_and=True):
        '''Return all of the results of a query in a list'''
        self.components_in_and = components_in_and
        return [obj for obj in iter(self)]
