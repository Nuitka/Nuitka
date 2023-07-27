#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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

import pkgutil
import sys
from abc import ABCMeta

# pylint: disable=invalid-name,self-assigning-variable

if str is bytes:
    import __builtin__ as builtins  # Python2 code, pylint: disable=import-error
else:
    import builtins

# Work around for CPython 3.x renaming "long" to "int".
if str is bytes:
    long = long  # Python2 code, pylint: disable=undefined-variable
else:
    long = int

# Work around for CPython 3.x renaming "unicode" to "str".
if str is bytes:
    unicode = unicode  # Python2 code, pylint: disable=undefined-variable
else:
    unicode = str


if str is bytes:

    def iterItems(d):
        return d.iteritems()

else:

    def iterItems(d):
        return d.items()


if str is not bytes:
    raw_input = input
    xrange = range
    basestring = str
else:
    raw_input = raw_input
    xrange = xrange
    basestring = basestring


if str is bytes:
    from urllib import (  # pylint: disable=I0021,import-error,no-name-in-module
        urlretrieve,
    )
else:
    from urllib.request import urlretrieve

if str is bytes:
    from cStringIO import StringIO  # Python2 code, pylint: disable=import-error
else:
    from io import StringIO

if str is bytes:
    BytesIO = StringIO
else:
    from io import BytesIO

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


if str is bytes:
    # Python2 only code, pylint: disable=deprecated-class,no-name-in-module
    from collections import Iterable, MutableSet
else:
    from collections.abc import Iterable, MutableSet

if str is bytes:
    intern = intern  # Python2 code, pylint: disable=undefined-variable
else:
    intern = sys.intern

if str is bytes:
    to_byte = chr
    from_byte = ord
else:

    def to_byte(value):
        assert type(value) is int and 0 <= value < 256
        return bytes((value,))

    def from_byte(value):
        assert type(value) is bytes and len(value) == 1, value
        return value[0]


try:
    from typing import GenericAlias
except ImportError:
    GenericAlias = None

try:
    from types import UnionType
except ImportError:
    UnionType = None


def getMetaClassBase(meta_class_prefix):
    """For Python2/3 compatible source, we create a base class that has the metaclass
    used and doesn't require making a choice.
    """

    class MetaClass(ABCMeta):
        pass

    MetaClassBase = MetaClass("%sMetaClassBase" % meta_class_prefix, (object,), {})

    return MetaClassBase


if str is bytes:
    try:
        import subprocess32 as subprocess
    except ImportError:
        import subprocess
else:
    import subprocess

# Just to make this not Windows-specific.
WindowsError = OSError  # pylint: disable=I0021,redefined-builtin

# Make it available for Python2 as well
PermissionError = (  # pylint: disable=redefined-builtin
    PermissionError if str is not bytes else OSError
)

if not hasattr(pkgutil, "ModuleInfo"):
    # Python3.5 or lower do not return namedtuple, but it's nicer to read code with it.
    from collections import namedtuple

    ModuleInfo = namedtuple("ModuleInfo", "module_finder name ispkg")

    def iter_modules(path=None, prefix=""):
        for item in pkgutil.iter_modules(path, prefix):
            yield ModuleInfo(*item)

else:
    iter_modules = pkgutil.iter_modules


try:
    ExceptionGroup = ExceptionGroup
except NameError:
    ExceptionGroup = None

try:
    BaseExceptionGroup = BaseExceptionGroup
except NameError:
    BaseExceptionGroup = None

# For PyLint to be happy.
assert long
assert unicode
assert urlretrieve
assert StringIO
assert BytesIO
assert type(xrange) is type, xrange
assert total_ordering
assert intern
assert builtins
assert Iterable
assert MutableSet
assert subprocess
assert GenericAlias or intern
assert UnionType or intern
