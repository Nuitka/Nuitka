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

"""Variable type for path Variables.

To be used whenever a user-specified path override setting should be allowed.

Arguments to PathVariable are:
  * *key* - name of this option on the command line (e.g. "prefix")
  * *help* - help string for option
  * *default* - default value for this option
  * *validator* - [optional] validator for option value.  Predefined are:

    * *PathAccept* - accepts any path setting; no validation
    * *PathIsDir* - path must be an existing directory
    * *PathIsDirCreate* - path must be a dir; will create
    * *PathIsFile* - path must be a file
    * *PathExists* - path must exist (any type) [default]

  The *validator* is a function that is called and which should return
  True or False to indicate if the path is valid.  The arguments
  to the validator function are: (*key*, *val*, *env*).  *key* is the
  name of the option, *val* is the path specified for the option,
  and *env* is the environment to which the Options have been added.

Usage example::

    opts = Variables()
    opts.Add(
        PathVariable(
            'qtdir',
            help='where the root of Qt is installed',
            default=qtdir,
            validator=PathIsDir,
        )
    )
    opts.Add(
        PathVariable(
            'qt_includes',
            help='where the Qt includes are installed',
            default='$qtdir/includes',
            validator=PathIsDirCreate,
        )
    )
    opts.Add(
        PathVariable(
            'qt_libraries',
            help='where the Qt library is installed',
            default='$qtdir/lib',
        )
    )
"""


import os
import os.path
from typing import Tuple, Callable

import SCons.Errors

__all__ = ['PathVariable',]

class _PathVariableClass:

    @staticmethod
    def PathAccept(key, val, env) -> None:
        """Accepts any path, no checking done."""
        pass

    @staticmethod
    def PathIsDir(key, val, env) -> None:
        """Validator to check if Path is a directory."""
        if not os.path.isdir(val):
            if os.path.isfile(val):
                m = 'Directory path for option %s is a file: %s'
            else:
                m = 'Directory path for option %s does not exist: %s'
            raise SCons.Errors.UserError(m % (key, val))

    @staticmethod
    def PathIsDirCreate(key, val, env) -> None:
        """Validator to check if Path is a directory,
           creating it if it does not exist."""
        try:
            os.makedirs(val, exist_ok=True)
        except FileExistsError:
            m = 'Path for option %s is a file, not a directory: %s'
            raise SCons.Errors.UserError(m % (key, val))
        except PermissionError:
            m = 'Path for option %s could not be created: %s'
            raise SCons.Errors.UserError(m % (key, val))

    @staticmethod
    def PathIsFile(key, val, env) -> None:
        """Validator to check if Path is a file"""
        if not os.path.isfile(val):
            if os.path.isdir(val):
                m = 'File path for option %s is a directory: %s'
            else:
                m = 'File path for option %s does not exist: %s'
            raise SCons.Errors.UserError(m % (key, val))

    @staticmethod
    def PathExists(key, val, env) -> None:
        """Validator to check if Path exists"""
        if not os.path.exists(val):
            m = 'Path for option %s does not exist: %s'
            raise SCons.Errors.UserError(m % (key, val))

    def __call__(self, key, help, default, validator=None) -> Tuple[str, str, str, Callable, None]:
        """Return a tuple describing a path list SCons Variable.

        The input parameters describe a 'path list' option. Returns
        a tuple with the correct converter and validator appended. The
        result is usable for input to :meth:`Add`.

        The *default* option specifies the default path to use if the
        user does not specify an override with this option.

        *validator* is a validator, see this file for examples
        """
        if validator is None:
            validator = self.PathExists

        if SCons.Util.is_List(key) or SCons.Util.is_Tuple(key):
            helpmsg = '%s ( /path/to/%s )' % (help, key[0])
        else:
            helpmsg = '%s ( /path/to/%s )' % (help, key)
        return (key, helpmsg, default, validator, None)


PathVariable = _PathVariableClass()

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
