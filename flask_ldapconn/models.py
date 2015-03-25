# -*- coding: utf-8 -*-
import json

from six import add_metaclass
from copy import deepcopy
from flask import current_app
from ldap3 import LDAPEntryError
from ldap3 import ObjectDef, Reader
from ldap3 import SUBTREE, STRING_TYPES
from ldap3.utils.conv import check_json_dict, format_json

from .attributes import LDAPAttribute


__all__ = ('LDAPEntry',)


class LDAPEntryMeta(type):

    base_dn = None
    search_scope = SUBTREE
    object_classes = ['top']

    def __init__(cls, name, bases, ns):
        cls._attributes = dict()
        cls._object_def = ObjectDef(cls.object_classes)

        # loop through the namespace looking for LDAPAttribute instances
        for key, value in ns.items():
            if isinstance(value, LDAPAttribute):
                cls._attributes[key] = value
                attr_def = value.get_abstract_attr_def(key)
                cls._object_def.add(attr_def)

    def get_new_class(cls):
        class_dict = deepcopy(cls()._attributes)
        new_cls = type(cls.__name__, (LDAPEntry,), class_dict)
        return new_cls


@add_metaclass(LDAPEntryMeta)
class LDAPEntry(object):

    def __init__(self, dn=None, **kwargs):
        self.__dict__['_dn'] = dn

        for key, value in kwargs.items():
            setattr(self, key, value)

    def __getitem__(self, item):
        return self.__getattr__(item)

    def __getattr__(self, item):
        if item not in self._attributes:
            raise LDAPEntryError('attribute not found')

        return getattr(self._attributes, item)

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __setattr__(self, key, value):
        if key not in self._attributes:
            raise LDAPEntryError('attribute not found')

        if isinstance(value, STRING_TYPES):
            value = [value]

        self._attributes[key].value = value

    @property
    def dn(self):
        return self._dn

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
        return ldapc.authenticate(self.dn, password)

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
        object_def = getattr(cls, '_object_def')

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
            new_cls = cls.get_new_class()
            model = new_cls(dn=entry.entry_get_dn(),
                            **entry.entry_get_attributes_dict())
            entries.append(model)
        return entries

    def get_attributes_dict(self):
        attr_dict = dict()
        for attr in self._attributes.keys():
            attr_dict.update({attr: getattr(self, attr)})
        return attr_dict

    def to_json(self, indent=2, sort=True):
        json_entry = dict()
        json_entry['dn'] = self.dn
        json_entry['attributes'] = self.get_attributes_dict()

        if str == bytes:
            check_json_dict(json_entry)

        json_output = json.dumps(json_entry, ensure_ascii=True, sort_keys=sort,
                                 indent=indent, check_circular=True,
                                 default=format_json, separators=(',', ': '))

        return json_output


LDAPModel = LDAPEntry
