# -*- coding: utf-8 -*-
import json

from six import add_metaclass
from copy import deepcopy
from flask import current_app
from ldap3 import ObjectDef
from ldap3 import LDAPEntryError
from ldap3 import STRING_TYPES
from ldap3.utils.conv import check_json_dict, format_json

from .query import BaseQuery
from .attribute import LDAPAttribute


__all__ = ('LDAPEntry',)


class LDAPEntryMeta(type):

    _changetype = 'add'

    base_dn = None
    sub_tree = True
    object_classes = ['top']
    operational_attributes = False

    def __init__(cls, name, bases, ns):
        cls._attributes = dict()
        cls._object_def = ObjectDef(cls.object_classes)

        # loop through the namespace looking for LDAPAttribute instances
        for key, value in ns.items():
            if isinstance(value, LDAPAttribute):
                cls._attributes[key] = value
                attr_def = value.get_abstract_attr_def(key)
                cls._object_def.add(attr_def)

    def get_new_type(cls):
        class_dict = deepcopy(cls()._attributes)
        new_cls = type(cls.__name__, (LDAPEntry,), class_dict)
        return new_cls

    @property
    def query(cls):
        return BaseQuery(cls)


@add_metaclass(LDAPEntryMeta)
class LDAPEntry(object):

    def __init__(self, dn=None, **kwargs):
        self.__dict__['_dn'] = dn

        for key, value in kwargs.items():
            setattr(self, key, value)

    def __iter__(self):
        for attribute in self._attributes:
            yield self._attributes[attribute]

    def __contains__(self, item):
        return True if self.__getitem__(item) else False

    def __getitem__(self, item):
        return self.__getattr__(item)

    def __getattr__(self, item):
        if item not in self._attributes:
            return None

        return self._attributes[item]

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __setattr__(self, key, value):
        if key not in self._attributes:
            raise LDAPEntryError('attribute not found')

#        if isinstance(value, STRING_TYPES):
#            value = [value]

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

    def get_attributes_dict(self):
        return dict((attribute_key, attribute_value.values) for (attribute_key,
                    attribute_value) in self._attributes.items())

    def to_json(self, indent=2, sort=True):
        json_entry = dict()
        json_entry['dn'] = self.dn
        json_entry['attributes'] = self.get_attributes_dict()

        if str == bytes:
            check_json_dict(json_entry)

        json_output = json.dumps(json_entry,
                                 ensure_ascii=True,
                                 sort_keys=sort,
                                 indent=indent,
                                 check_circular=True,
                                 default=format_json,
                                 separators=(',', ': '))

        return json_output


LDAPModel = LDAPEntry
