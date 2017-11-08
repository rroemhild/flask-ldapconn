Changelog
=========

0.7.0 (2017-11-09)
------------------
* Allow model inheritance (Dominik George)
* Fix/revisit attribute access (Dominik George)
* Update ldap3 to version 2.3
* Update Flaks to 0.12

0.6.13 (2016-05-30)
-------------------
* Fix get entries with multivalued RDNs
* Update ldap3 to version 1.3.1

0.6.12 (2016-04-03)
-------------------
* Update ldap3 to version 1.2.2
* Dropped support for Python 3.3

0.6.11 (2016-01-28)
-------------------
* Use components_in_and flag in Reader object
* Update ldap3 to version 1.0.4

0.6.10 (2015-12-15)
-------------------
* Update ldap3 to version 1.0.3

0.6.9 (2015-12-15)
------------------
* Update ldap3 to version 1.0.2

0.6.8 (2015-12-07)
------------------
* Add read-only option
* Update ldap3 to version 1.0.1


0.6.7 (2015-10-11)
------------------
* Use connections saved on flask.g.ldap_conn

0.6.6 (2015-10-8)
------------------
* Return manager class in queries instead of fix LDAPEntry class
* Update six 1.9.0 -> 1.10.0

0.6.5
-----
* Update ldap3 to version 0.9.9.1

0.6.4 (2015-08-16)
------------------
* Update ldap3 to version 0.9.8.8

0.6.3 (2015-07-07)
------------------
* Update ldap3 to version 0.9.8.6

0.6.2 (2015-06-21)
------------------
* Fix TLS settings

0.6.1 (2015-05-29)
------------------
* Update ldap3 to v0.9.8.4

0.6 (2015-03-31)
----------------
* Refactored the LDAPModel class
* LDAPModel is now LDAPEntry
* Add write operation save (add, modify) and delete
* LDAPEntry now use a query class to simplify ldap query

0.5.2 (2015-03-11)
------------------
* LDAPModel classes can now be instantiated with arguments.

0.5.1 (2015-03-11)
------------------
* Fixed installer problem. Handle flask-ldapconn as package.
* Refactored the LDAPModel class

0.5 (2015-03-07)
----------------
* Refactored the LDAPModel class

0.4 (2015-03-07)
----------------
* Add authentication method
* Deprecate mapped connection methods
* Update Flask to 0.10.1 and ldap3 to 0.9.7.10

0.3.4
-----
* v0.3.4: Add configuration option for SSL (Bartosz Marcinkowski)
* v0.3.4: Add support for Python 3 (Bartosz Marcinkowski)
* v0.3.4: Update python-ldap3 to v0.9.7.5

0.3.3
-----
* v0.3.3: Allow anonymous auth

0.3.2
-----
* v0.3.2: BUGFIX: Allow unsecure connections

0.3.1
------
* v0.3.1: Return entries instead of Reader object in models

0.3 (2015-02-10)
----------------
* Add simple read-only class model

0.2 (2015-02-05)
----------------
* Switch to python-ldap3

0.1 (2015-02-02)
----------------
* Conception
* Initial Commit of Package to GitHub
