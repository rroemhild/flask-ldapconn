# -*- coding: utf-8 -*-

'''
Flask-LDAPConn
--------------

Flask extension providing ldap3 connection object for accessing LDAP servers.
'''

import sys

from setuptools import setup


setup(
    name='Flask-LDAPConn',
    version='0.3',
    url='http://github.com/rroemhild/flask-ldapconn',
    license='BSD',
    author='Rafael Römhild',
    author_email='rafael@roemhild.de',
    keywords='flask ldap ldap3',
    description='Basic, pure python, LDAP connection for Flask Applications',
    long_description=open('README.rst').read(),
    py_modules=[
        'flask_ldapconn'
    ],
    package_data={'': ['LICENSE']},
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask>=0.9',
        'ldap3>=0.9.7.4'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)

