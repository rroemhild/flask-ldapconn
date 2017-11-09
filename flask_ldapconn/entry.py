# -*- coding: utf-8 -*-
import json

from six import add_metaclass
from copy import deepcopy
from importlib import import_module

from flask import current_app
from ldap3 import ObjectDef
from ldap3.core.exceptions import LDAPAttributeError
from ldap3.utils.dn import safe_dn
from ldap3.utils.conv import check_json_dict, format_json

from .query import BaseQuery
from .attribute import LDAPAttribute


__all__ = ('LDAPEntry',)


class LDAPEntryMeta(type):

    # requiered
    base_dn = None
    entry_rdn = ['cn']
    object_classes = ['top']

    # optional
    sub_tree = True
    operational_attributes = False

    def __init__(cls, name, bases, ns):
        cls._attributes = dict()

        # Merge attributes and object classes from parents
        for base in bases:
            if isinstance(base, LDAPEntryMeta):
                cls._attributes.update(base._attributes)
                # Deduplicate object classes
                cls.object_classes = list(
                    set(cls.object_classes + base.object_classes))

        # Create object definition
        cls._object_def = ObjectDef(cls.object_classes)

        # loop through the namespace looking for LDAPAttribute instances
        for key, value in ns.items():
            if isinstance(value, LDAPAttribute):
                cls._attributes[key] = value

        # Generate attribute definitions
        for key in cls._attributes:
            attr_def = cls._attributes[key].get_abstract_attr_def(key)
            cls._object_def.add_attribute(attr_def)

    @property
    def query(cls):
        return BaseQuery(cls)

    def get_new_type(cls):
        class_dict = deepcopy(cls()._attributes)
        module = import_module(cls.__module__)
        obj = getattr(module, cls.__name__)
        new_cls = type(cls.__name__, (obj,), class_dict)
        return new_cls


@add_metaclass(LDAPEntryMeta)
class LDAPEntry(object):

    def __init__(self, dn=None, changetype='add', **kwargs):
        self.__dict__['_dn'] = dn
        self.__dict__['_changetype'] = changetype

        for key, value in kwargs.items():
            if key not in self._attributes:
                raise LDAPAttributeError('attribute not found')
            self._attributes[key]._init = value

    def __iter__(self):
        for attribute in self._attributes:
            yield self._attributes[attribute]

    def __contains__(self, item):
        return item in self._attributes

    def __getitem__(self, item):
        if item in self.__attributes:
            return self.__getattr__(item)
        else:
            raise KeyError(item)

    def __getattribute__(self, item):
        if item != '_attributes' and item in self._attributes:
            return self._attributes[item].value
        else:
            return object.__getattribute__(self, item)

    def __setitem__(self, key, value):
        if key in self._attributes:
            self.__setattr__(key, value)
        else:
            raise KeyError(key)

    def __setattr__(self, key, value):
        if key in self._attributes:
            self._attributes[key].value = value
        else:
            return object.__setattr__(self, key, value)

    @property
    def dn(self):
        if self._dn is None:
            self.generate_dn_from_entry()
        return self._dn

    def generate_dn_from_entry(self):
        rdn_list = list()
        for attr in self._object_def:
            if attr.name in self.entry_rdn:
                if len(self._attributes[attr.key]) == 1:
                    rdn = '{attr}={value}'.format(
                        attr=attr.name,
                        value=self._attributes[attr.key].value
                    )
                    rdn_list.append(rdn)

        dn = '{rdn},{base_dn}'.format(rdn='+'.join(rdn_list),
                                      base_dn=self.base_dn)

        self.__dict__['_dn'] = safe_dn(dn)

    def get_attributes_dict(self):
        return dict((attribute_key, attribute_value.values) for (attribute_key,
                    attribute_value) in self._attributes.items())

    def get_entry_add_dict(self, attr_dict):
        add_dict = dict()
        for attribute_key, attribute_value in attr_dict.items():
            if self._attributes[attribute_key].value:
                attribute_def = self._object_def[attribute_key]
                add_dict.update({attribute_def.name: attribute_value})
        return add_dict

    def get_entry_modify_dict(self, attr_dict):
        modify_dict = dict()
        for attribute_key in attr_dict.keys():
            if self._attributes[attribute_key].changetype is not None:
                attribute_def = self._object_def[attribute_key]
                changes = self._attributes[attribute_key].get_changes_tuple()
                modify_dict.update({attribute_def.name: changes})
        return modify_dict

    @property
    def connection(self):
        return current_app.extensions.get('ldap_conn')

    def delete(self):
        '''Delete this entry from LDAP server'''
        self.connection.connection.delete(self.dn)

    def save(self):
        '''Save the current instance'''
        attributes = self.get_entry_add_dict(self.get_attributes_dict())
        if self._changetype is 'add':
            return self.connection.connection.add(self.dn,
                                                  self.object_classes,
                                                  attributes)
        elif self._changetype == 'modify':
            changes = self.get_entry_modify_dict(self.get_attributes_dict())
            return self.connection.connection.modify(self.dn, changes)

        return False

    def authenticate(self, password):
        '''Authenticate a user with an LDAPModel class

        Args:
            password (str): The user password.

        '''
        return self.connection.authenticate(self.dn, password)

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
