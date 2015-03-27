# -*- coding: utf-8 -*-
from ldap3 import AttrDef, LDAPAttributeError, STRING_TYPES


class LDAPAttribute(object):

    def __init__(self, name, validate=None, default=None, dereference_dn=None):
        self.__dict__['values'] = []
        self.__dict__['name'] = name
        self.__dict__['validate'] = validate
        self.__dict__['default'] = default
        self.__dict__['dereference_dn'] = dereference_dn

    def __str__(self):
        return self.value

    def __len__(self):
        return len(self.values)

    def __iter__(self):
        return self.values.__iter__()

    def __setattr__(self, item, value):
        if item is not 'value':
            raise LDAPAttributeError('can not set key')

        if isinstance(value, STRING_TYPES):
            value = [value]
        self.__dict__['values'] = value

    @property
    def value(self):
        '''Return the single value or a list of values of the attribute.'''
        if len(self.__dict__['values']) == 1:
            return self.__dict__['values'][0]
        else:
            return self.__dict__['values']

    def get_abstract_attr_def(self, key):
        return AttrDef(name=self.name, key=key,
                       validate=self.validate,
                       default=self.default,
                       dereference_dn=self.dereference_dn)
