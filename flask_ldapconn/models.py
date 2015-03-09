# -*- coding: utf-8 -*-
from flask import current_app
from ldap3 import AttrDef, ObjectDef, Reader, SUBTREE, Entry

from .attributes import LDAPAttribute


__all__ = ('LDAPModel',)


class LDAPModel(Entry):
    '''Base class for all LDAP models

    Args:
        entry (ldap3.Entry): An Entry object from Reader search result.
    '''

    base_dn = None
    search_scope = SUBTREE
    object_classes = ['top']

    def __init__(self, entry=None):
        super(LDAPModel, self).__init__(dn=None, reader=None)
        if entry is None:
            for key in dir(self):
                attr = getattr(self, key)
                if not isinstance(attr, LDAPAttribute):
                    continue
                self.__dict__['_attributes'][key] = attr
        else:
            self.__dict__['_dn'] = entry.entry_get_dn()
            self.__dict__['_raw_attributes'] = entry._raw_attributes
            for attr in entry:
                attr_def = getattr(attr, 'definition')
                new_attr = LDAPAttribute(attr.key, attr_def=attr_def)
                new_attr.value = attr.value
                self.__dict__['_attributes'][attr.key] = new_attr

    def __setattr__(self, item, value):
        self._attributes[item].value = value

    def delete(self):
        '''Delete this entry from LDAP server
        '''
        pass

    def save(self):
        '''Save the current instance
        '''
        pass

    def authenticate(self, password):
        '''Authenticate a user with an LDAPModel class

        Args:
            password (str): The user password.

        '''
        app = current_app._get_current_object()
        ldapc = app.extensions.get('ldap_conn')
        return ldapc.authenticate(self.entry_get_dn(), password)

    @classmethod
    def fetch(self, attribute, value, search_filter=None):
        '''Return the first entry from a attribute=value search

        Args:
            attribute (str): Perfom search with attribute.
            value (str): The value in attribute.
            query (str): Standard LDAP filter.

        Return:
            entry (LDAPConn.LDAPModel): The first entry from the search
                response or None.
        '''
        query = '({0}={1})'.format(attribute, value)
        if search_filter is not None:
            query = '(&{0}{1})'.format(query, search_filter)

        try:
            entries = self.search(query)
            return entries[0]
        except IndexError:
            return None

    @classmethod
    def search(cls, query):
        '''Perform searches with a ldap3.Reader instance

        Args:
            query (str): A simplified query or a standard LDAP filter.

        Returns:
            list: A List of LDAPConn.LDAPModel objects.
        '''
        entries = []
        base_dn = getattr(cls, 'base_dn')
        search_scope = getattr(cls, 'search_scope')
        object_def = cls.get_abstract_object_def()

        app = current_app._get_current_object()
        ldapc = app.extensions.get('ldap_conn')
        reader = Reader(connection=ldapc.connection,
                        object_def=object_def,
                        query=query,
                        base=base_dn,
                        components_in_and=True,
                        sub_tree=search_scope,
                        get_operational_attributes=False,
                        controls=None)
        reader.search()
        for entry in reader.entries:
            entries.append(LDAPModel(entry))
        return entries

    @classmethod
    def get_abstract_object_def(cls):
        object_def = ObjectDef(getattr(cls, 'object_classes'))
        for key in dir(cls):
            attr = getattr(cls, key)
            if not isinstance(attr, LDAPAttribute):
                continue
            attr_def = AttrDef(
                name=attr.name,
                key=key,
                validate=attr.validate,
                pre_query=attr.pre_query,
                post_query=attr.post_query,
                default=attr.default,
                dereference_dn=attr.dereference_dn,
            )
            object_def.add(attr_def)
        return object_def
