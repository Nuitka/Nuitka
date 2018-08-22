#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
"""
Module like __future__ for things that are changed between Python2 and Python3.

These are here to provide compatible fall-backs. This is required to run the
same code easily with both CPython2 and CPython3. Sometimes, we do not care
about the actual types, or API, but would rather just check for something to
be a "in (str, unicode)" rather than making useless version checks.

"""

import sys

# pylint: disable=I0021,invalid-name,redefined-builtin

# Work around for CPython 3.x renaming "long" to "int".
try:
    long = long  # @ReservedAssignment
except NameError:
    long = int   # @ReservedAssignment

# Work around for CPython 3.x renaming "unicode" to "str".
try:
    unicode = unicode  # @ReservedAssignment
except NameError:
    unicode = str      # @ReservedAssignment

def iterItems(d):
    try:
        return d.iteritems()
    except AttributeError:
        return d.items()

try:
    raw_input = raw_input  # @ReservedAssignment
except NameError:
    raw_input = input      # @ReservedAssignment

try:
    xrange = xrange  # @ReservedAssignment
except NameError:
    xrange = range   # @ReservedAssignment

try:
    from urllib.request import urlretrieve  # @UnresolvedImport
except ImportError:
    from urllib import urlretrieve          # @UnresolvedImport

try:
    from cStringIO import StringIO  # @UnresolvedImport
except ImportError:
    from io import StringIO         # @UnresolvedImport

try:
    from functools import total_ordering
except ImportError:
    # Lame replacement for functools.total_ordering, which does not exist on
    # Python2.6, this requires "<" and "=" and adds all other operations.
    def total_ordering(cls):
        cls.__ne__ = lambda self, other: not self == other
        cls.__le__ = lambda self, other: self == other or self < other
        cls.__gt__ = lambda self, other: self != other and not self < other
        cls.__ge__ = lambda self, other: self == other and not self < other

        return cls

try:
    intern = intern      # @ReservedAssignment
except NameError:
    intern = sys.intern  # @ReservedAssignment @UndefinedVariable

# For PyLint to be happy.
assert long
assert unicode
assert urlretrieve
assert StringIO
assert type(xrange) is type, xrange
assert total_ordering
assert intern
