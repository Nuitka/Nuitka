#
#     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#
"""engine.SCons.Variables.EnumVariable

This file defines the option type for SCons allowing only specified
input-values.

Usage example:

  opts = Variables()
  opts.Add(EnumVariable('debug', 'debug output and symbols', 'no',
                      allowed_values=('yes', 'no', 'full'),
                      map={}, ignorecase=2))
  ...
  if env['debug'] == 'full':
    ...
"""

#
# Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 The SCons Foundation
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
#

__revision__ = "src/engine/SCons/Variables/EnumVariable.py 5134 2010/08/16 23:02:40 bdeegan"

__all__ = ['EnumVariable',]


import SCons.Errors

def _validator(key, val, env, vals):
    if not val in vals:
        raise SCons.Errors.UserError(
            'Invalid value for option %s: %s' % (key, val))


def EnumVariable(key, help, default, allowed_values, map={}, ignorecase=0):
    """
    The input parameters describe a option with only certain values
    allowed. They are returned with an appropriate converter and
    validator appended. The result is usable for input to
    Variables.Add().

    'key' and 'default' are the values to be passed on to Variables.Add().

    'help' will be appended by the allowed values automatically

    'allowed_values' is a list of strings, which are allowed as values
    for this option.

    The 'map'-dictionary may be used for converting the input value
    into canonical values (eg. for aliases).

    'ignorecase' defines the behaviour of the validator:

    If ignorecase == 0, the validator/converter are case-sensitive.
    If ignorecase == 1, the validator/converter are case-insensitive.
    If ignorecase == 2, the validator/converter is case-insensitive and
                        the converted value will always be lower-case.

    The 'validator' tests whether the value is in the list of allowed
    values. The 'converter' converts input values according to the
    given 'map'-dictionary (unmapped input values are returned
    unchanged). 
    """
    help = '%s (%s)' % (help, '|'.join(allowed_values))
    # define validator
    if ignorecase >= 1:
        validator = lambda key, val, env: \
                    _validator(key, val.lower(), env, allowed_values)
    else:
        validator = lambda key, val, env: \
                    _validator(key, val, env, allowed_values)
    # define converter
    if ignorecase == 2:
        converter = lambda val: map.get(val.lower(), val).lower()
    elif ignorecase == 1:
        converter = lambda val: map.get(val.lower(), val)
    else:
        converter = lambda val: map.get(val, val)
    return (key, help, default, validator, converter)

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
