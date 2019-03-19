# -*- coding: utf-8 -*-
import sys
from flask import current_app
from ldap3 import BASE, Reader, SUBTREE, ObjectDef


__all__ = ('BaseQuery',)


class BaseQuery(object):

    def __init__(self, obj):
        self.obj = obj
        self.query = []
        self.base_dn = obj.base_dn
        self.sub_tree = obj.sub_tree
        self.object_def = ObjectDef(obj.object_classes)
        self.operational_attributes = obj.operational_attributes
        self.components_in_and = True

    def add_abstract_attr_def(self):
        for name, attr in self.obj._fields.items():
            attr_def = attr.get_abstract_attr_def(name)
            self.object_def.add_attribute(attr_def)

    def __iter__(self):
        for entry in self.get_reader_result():
            module = sys.modules.get(self.obj.__module__)
            new_cls = getattr(module, self.obj.__name__)
            ldapentry = new_cls(dn=entry.entry_dn,
                                changetype='modify',
                                **entry.entry_attributes_as_dict)
            yield ldapentry

    def get_reader_result(self):
        query = ','.join(self.query)
        ldapc = current_app.extensions.get('ldap_conn')
        self.add_abstract_attr_def()
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
