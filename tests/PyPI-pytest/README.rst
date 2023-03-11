################################################
 Automated Pytest Testing for Top PyPI Packages
################################################

**********
 Overview
**********

What it does
============

The ``run_all.py`` script automates the comparison of pytest results of
a nuitka compiled wheel using ``python setup.py bdist_nuitka`` to the
pytest results of an uncompiled wheel built using ``python setup.py
bdist_wheel`` for the most popular PyPI packages. Testing is done to
ensure that nuitka is building the wheel correctly. If the pytests
pass/fail in the same way, that means Nuitka built the wheel properly.
Else if the tests differ, then something is wrong. Virtualenv is used to
create a clean environment with no outside pollution. These tests are
meant to be run regularly and will inform if ``Nuitka`` experiences a
regression.

How it works
============

First, the script loads information from ``packages.json``. For each
package there, it goes to a local cache folder and either updates the
package or clones the package into cache using ``git``. The script then
creates a ``virtualenv`` and sets up for ``bdist_wheel``. A normal wheel
is built using the ``bdist_wheel`` command which is then installed.
Normal pytest is run for the package, and the output is captured into a
string. The script then resets the package to its original state and
sets up for ``bdist_nuitka``. A Nuitka-compiled wheel is then built
using the ``bdist_nuitka`` command which is then installed. Pytest is
run again for the package, and the output is captured into another
string. The two strings of pytest outputs are then compared to see if
any differences exist.

Packages.json
=============

The file containing the packages to be tested and their respective
information.

-  Attributes

   -  ``ignored_tests``: path of tests to be ignored, starting at the
      base package folder level
   -  ``[package_name]``: OPTIONAL, specified if a package has a
      different import package_name
   -  ``requirements_file``: filename containing requirements to be
      ``pip`` installed before pytest could be run
   -  ``url``: URL of the package to be ``git`` cloned or updated

*************
 Basic Usage
*************

Execute these commands to run all tests

#. ``cd`` into the current folder on terminal
#. ``python run_all.py``

******************
 Advanced Options
******************

The ``run_all.py`` script uses ``SearchModes``, which allows the user to
specify different options.

List of options
===============

-  ``all``

   Run testing for all packages, tallying the number of errors.

   -  Usage: ``python run_all.py all``

-  ``only``

   Run testing for only the package specified.

   -  Usage: ``python run_all.py only [PACKAGE]``
   -  Example: ``python run_all.py only click``

-  ``search``

   Run tests starting at the package specified, abort if an error is
   found

   -  Usage: ``python run_all.py search [PACKAGE]``
   -  Example: ``python run_all.py search click``

-  ``resume``

   Run tests starting at the package where it last left off

   -  Usage: ``python run_all.py resume``
