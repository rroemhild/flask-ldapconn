# -*- coding: utf-8 -*-
from ldap3 import Attribute, AttrDef, LDAPAttributeError


__all__ = ('LDAPAttribute',)


class LDAPAttribute(Attribute):
    '''Base class for all LDAP model attributes

    Args:
        name (str): LDAP Attribute name
        attr_def (ldap3.AttrDef): or None
    '''
    def __init__(self,
                 name,
                 validate=None,
                 pre_query=None,
                 post_query=None,
                 default=None,
                 dereference_dn=None,
                 attr_def=None):
        self.__dict__['name'] = name
        self.__dict__['validate'] = validate
        self.__dict__['pre_query'] = pre_query
        self.__dict__['post_query'] = post_query
        self.__dict__['default'] = default
        self.__dict__['dereference_dn'] = dereference_dn

        if attr_def is None:
            super(LDAPAttribute, self).__init__(AttrDef(name), None)
        else:
            super(LDAPAttribute, self).__init__(attr_def, None)

    def __setattr__(self, item, value):
        if item == 'value':
            if isinstance(value, str):
                self.__dict__['values'] = [value]
            else:
                self.__dict__['values'] = value
        else:
            raise LDAPAttributeError('attribute is read only')
