# -*- coding: utf-8 -*-

'''
Flask-LDAPConn
--------------

Flask extension providing ldap3 connection object and ORM
to accessing LDAP servers.
'''


from setuptools import setup


setup(
    name='Flask-LDAPConn',
    version='0.7.0',
    url='http://github.com/rroemhild/flask-ldapconn',
    license='BSD',
    author='Rafael Römhild',
    author_email='rafael@roemhild.de',
    keywords='flask ldap ldap3 orm',
    description='Pure python, LDAP connection and ORM for Flask Applications',
    long_description=open('README.rst').read(),
    packages=[
        'flask_ldapconn'
    ],
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask>=0.12',
        'ldap3>=2.3',
        'six>=1.10'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Framework :: Flask',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
