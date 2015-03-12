# -*- coding: utf-8 -*-
from flask import current_app
from ldap3 import AttrDef, ObjectDef, Reader, SUBTREE, Entry
from ldap3 import LDAPAttributeError

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

    def __init__(self, dn=None, raw_attributes=None, **kwargs):
        super(LDAPModel, self).__init__(dn=dn, reader=None)
        self.__dict__['_raw_attributes'] = raw_attributes

        # init attributes
        for key in dir(self):
            attr = getattr(self, key)
            if not isinstance(attr, LDAPAttribute):
                continue
            self.__dict__['_attributes'][key] = attr

        # set attributes data
        for key, value in kwargs.items():
            self[key].value = value

    def __setattr__(self, key, value):
        self[key].value = value

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
            entries.append(cls(
                           dn=entry.entry_get_dn(),
                           raw_attributes=entry.entry_get_raw_attributes(),
                           **entry.entry_get_attributes_dict()))
        return entries

    @classmethod
    def get_abstract_object_def(cls):
        object_def = ObjectDef(getattr(cls, 'object_classes'))
        for key in dir(cls):
            attr = getattr(cls, key)
            if not isinstance(attr, LDAPAttribute):
                continue
            attr_def = attr.get_abstract_attr_def(key)
            object_def.add(attr_def)
        return object_def
