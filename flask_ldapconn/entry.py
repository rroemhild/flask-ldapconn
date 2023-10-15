# -*- coding: utf-8 -*-
import json
from flask import current_app
from ldap3.utils.dn import safe_dn
from ldap3.utils.conv import check_json_dict, format_json
from ldap3.core.exceptions import LDAPAttributeError

from .query import BaseQuery
from .attribute import LDAPAttribute, LdapField


__all__ = ('LDAPEntry',)


class LDAPEntryMeta(type):

    def __init__(cls, name, bases, attr):
        cls._fields = {}
        for key, value in attr.items():
            if isinstance(value, LdapField):
                cls._fields[key] = value

        for base in bases:
            if isinstance(base, LDAPEntryMeta):
                cls._fields.update(base._fields)
                # Deduplicate object classes
                cls.object_classes = list(
                    set(cls.object_classes + base.object_classes))

    @property
    def query(cls):
        return BaseQuery(cls)


class LDAPEntry(object, metaclass=LDAPEntryMeta):

    base_dn = None
    entry_rdn = ['cn']
    object_classes = ['top']
    sub_tree = True
    operational_attributes = False
    _changetype = 'add'

    def __init__(self, dn=None, changetype='add', **kwargs):
        self._attributes = {}
        self._dn = dn
        self._changetype = changetype
        if kwargs:
            for key, value in kwargs.items():
                self._store_attr(key, value, init=True)
        for key, ldap_attr in self._fields.items():
            if not self._isstored(key):
                self._store_attr(key, [])

    @property
    def dn(self):
        if self._dn is None:
            self.generate_dn_from_entry()
        return self._dn

    def generate_dn_from_entry(self):
        rdn_list = list()
        for key, attr in self._attributes.items():
            if attr.name in self.entry_rdn:
                if len(self._attributes[key]) == 1:
                    rdn = '{attr}={value}'.format(
                        attr=attr.name,
                        value=self._attributes[key].value
                    )
                    rdn_list.append(rdn)
        dn = '{rdn},{base_dn}'.format(rdn='+'.join(rdn_list),
                                      base_dn=self.base_dn)
        self._dn = safe_dn(dn)

    @classmethod
    def _get_field(cls, attr):
        return cls._fields.get(attr)

    @classmethod
    def _get_field_name(cls, attr):
        if cls._get_field(attr):
            return cls._get_field(attr).name

    def _store_attr(self, attr, value=[], init=False):
        if not self._get_field(attr):
            raise LDAPAttributeError('attribute not found')
        if value is None:
            value = []
        if not self._attributes.get(attr):
            self._attributes[attr] = LDAPAttribute(self._get_field_name(attr))
        self._attributes[attr].value = value
        if init:
            self._attributes[attr].__dict__['changetype'] = None

    def _isstored(self, attr):
        return self._attributes.get(attr)

    def _get_attr(self, attr):
        if self._isstored(attr):
            return self._attributes[attr].value
        return None

    def __getattribute__(self, item):
        if item != '_fields' and item in self._fields:
            return self._get_attr(item)
        return super(LDAPModel, self).__getattribute__(item)

    def __setattr__(self, key, value):
        if key != '_fields' and key in self._fields:
            self._store_attr(key, value)
        else:
            return super(LDAPModel, self).__setattr__(key, value)

    def get_attributes_dict(self):
        return dict((attribute_key, attribute_value.values) for (attribute_key,
                    attribute_value) in self._attributes.items())

    def get_entry_add_dict(self, attr_dict):
        add_dict = dict()
        for attribute_key, attribute_value in attr_dict.items():
            if self._attributes[attribute_key].value != []:
                add_dict.update({self._get_field_name(attribute_key): attribute_value})
        return add_dict

    def get_entry_modify_dict(self, attr_dict):
        modify_dict = dict()
        for attribute_key in attr_dict.keys():
            if self._attributes[attribute_key].changetype is not None:
                changes = self._attributes[attribute_key].get_changes_tuple()
                modify_dict.update({self._get_field_name(attribute_key): changes})
        return modify_dict

    @property
    def connection(self):
        return current_app.extensions.get('ldap_conn')

    def delete(self):
        '''Delete this entry from LDAP server'''
        return self.connection.connection.delete(self.dn)

    def save(self):
        '''Save the current instance'''
        attrs = self.get_attributes_dict()
        if self._changetype == 'add':
            changes = self.get_entry_add_dict(attrs)
            return self.connection.connection.add(self.dn,
                                                  self.object_classes,
                                                  changes)
        elif self._changetype == 'modify':
            changes = self.get_entry_modify_dict(attrs)
            return self.connection.connection.modify(self.dn, changes)

        return False

    def authenticate(self, password):
        '''Authenticate a user with an LDAPModel class

        Args:
            password (str): The user password.

        '''
        return self.connection.authenticate(self.dn, password)

    def to_json(self, indent=2, sort=True, str_values=False):
        json_entry = dict()
        json_entry['dn'] = self.dn

        # Get "single values" from attributes as str instead list if
        # `str_values=True` else get all attributes as list. This only
        # works if `FORCE_ATTRIBUTE_VALUE_AS_LIST` is False (default).
        if str_values is True:
            json_entry['attributes'] = {}
            for attr in self._attributes.keys():
                json_entry['attributes'][attr] = self._attributes[attr].value
        else:
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
