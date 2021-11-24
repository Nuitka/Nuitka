# MIT License
#
# Copyright The SCons Foundation
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""SCons compatibility package for old Python versions

This subpackage holds modules that provide backwards-compatible
implementations of various things from newer Python versions
that we cannot count on because SCons still supported older Pythons.

Other code will not generally reference things in this package through
the SCons.compat namespace.  The modules included here add things to
the builtins namespace or the global module list so that the rest
of our code can use the objects and names imported here regardless of
Python version. As a result, if this module is used, it should violate
the normal convention for imports (standard library imports first,
then program-specific imports, each ordered aplhabetically)
and needs to be listed first.

The rest of the things here will be in individual compatibility modules
that are either: 1) suitably modified copies of the future modules that
we want to use; or 2) backwards compatible re-implementations of the
specific portions of a future module's API that we want to use.

GENERAL WARNINGS:  Implementations of functions in the SCons.compat
modules are *NOT* guaranteed to be fully compliant with these functions in
later versions of Python.  We are only concerned with adding functionality
that we actually use in SCons, so be wary if you lift this code for
other uses.  (That said, making these more nearly the same as later,
official versions is still a desirable goal, we just don't need to be
obsessive about it.)

We name the compatibility modules with an initial '_scons_' (for example,
_scons_subprocess.py is our compatibility module for subprocess) so
that we can still try to import the real module name and fall back to
our compatibility module if we get an ImportError.  The import_as()
function defined below loads the module as the "real" name (without the
'_scons'), after which all of the "import {module}" statements in the
rest of our code will find our pre-loaded compatibility module.
"""

import sys
import importlib

PYPY = hasattr(sys, 'pypy_translation_info')


def rename_module(new, old):
    """
    Attempt to import the old module and load it under the new name.
    Used for purely cosmetic name changes in Python 3.x.
    """
    try:
        sys.modules[new] = importlib.import_module(old)
        return True
    except ImportError:
        return False


# Default pickle protocol. Higher protocols are more efficient/featured
# but incompatible with older Python versions.
# Negative numbers choose the highest available protocol.

# Was pickle.HIGHEST_PROTOCOL
# Changed to 4 so that python 3.8's not incompatible with previous versions
# Python 3.8 introduced protocol 5 which is mainly an improvement for for out-of-band data buffers
PICKLE_PROTOCOL = 4


class NoSlotsPyPy(type):
    """ Metaclass for PyPy compatitbility.

    PyPy does not work well with __slots__ and __class__ assignment.
    """

    def __new__(meta, name, bases, dct):
        if PYPY and '__slots__' in dct:
            dct.pop('__slots__')
        return super(NoSlotsPyPy, meta).__new__(meta, name, bases, dct)

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
