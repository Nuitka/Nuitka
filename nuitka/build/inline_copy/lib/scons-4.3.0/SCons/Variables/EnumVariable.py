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

"""Variable type for enumeration Variables.

Enumeration variables allow selection of one from a specified set of values.

Usage example::

    opts = Variables()
    opts.Add(
        EnumVariable(
            'debug',
            help='debug output and symbols',
            default='no',
            allowed_values=('yes', 'no', 'full'),
            map={},
            ignorecase=2,
        )
    )
    ...
    if env['debug'] == 'full':
    ...
"""

from typing import Tuple, Callable

import SCons.Errors

__all__ = ['EnumVariable',]


def _validator(key, val, env, vals) -> None:
    if val not in vals:
        raise SCons.Errors.UserError(
            'Invalid value for option %s: %s.  Valid values are: %s' % (key, val, vals))


def EnumVariable(key, help, default, allowed_values, map={}, ignorecase=0) -> Tuple[str, str, str, Callable, Callable]:
    """Return a tuple describing an enumaration SCons Variable.

    The input parameters describe an option with only certain values
    allowed. Returns A tuple including an appropriate converter and
    validator. The result is usable as input to :meth:`Add`.

    *key* and *default* are passed directly on to :meth:`Add`.

    *help* is the descriptive part of the help text,
    and will have the allowed values automatically appended.

    *allowed_values* is a list of strings, which are the allowed values
    for this option.

    The *map*-dictionary may be used for converting the input value
    into canonical values (e.g. for aliases).

    The value of *ignorecase* defines the behaviour of the validator:

        * 0: the validator/converter are case-sensitive.
        * 1: the validator/converter are case-insensitive.
        * 2: the validator/converter is case-insensitive and the
          converted value will always be lower-case.

    The *validator* tests whether the value is in the list of allowed values.
    The *converter* converts input values according to the given
    *map*-dictionary (unmapped input values are returned unchanged).
    """

    help = '%s (%s)' % (help, '|'.join(allowed_values))
    # define validator
    if ignorecase:
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
