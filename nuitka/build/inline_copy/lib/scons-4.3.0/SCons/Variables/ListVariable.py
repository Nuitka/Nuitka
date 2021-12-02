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

"""Variable type for list Variables.

A 'list' option may either be 'all', 'none' or a list of names
separated by comma. After the option has been processed, the option
value holds either the named list elements, all list elements or no
list elements at all.

Usage example::

    list_of_libs = Split('x11 gl qt ical')

    opts = Variables()
    opts.Add(
        ListVariable(
            'shared',
            help='libraries to build as shared libraries',
            default='all',
            elems=list_of_libs,
        )
    )
    ...
    for lib in list_of_libs:
        if lib in env['shared']:
            env.SharedObject(...)
        else:
            env.Object(...)
"""

# Known Bug: This should behave like a Set-Type, but does not really,
# since elements can occur twice.

import collections
from typing import Tuple, Callable

import SCons.Util

__all__ = ['ListVariable',]


class _ListVariable(collections.UserList):
    def __init__(self, initlist=None, allowedElems=None):
        if initlist is None:
            initlist = []
        if allowedElems is None:
            allowedElems = []
        super().__init__([_f for _f in initlist if _f])
        self.allowedElems = sorted(allowedElems)

    def __cmp__(self, other):
        raise NotImplementedError

    def __eq__(self, other):
        raise NotImplementedError

    def __ge__(self, other):
        raise NotImplementedError

    def __gt__(self, other):
        raise NotImplementedError

    def __le__(self, other):
        raise NotImplementedError

    def __lt__(self, other):
        raise NotImplementedError

    def __str__(self):
        if not len(self):
            return 'none'
        self.data.sort()
        if self.data == self.allowedElems:
            return 'all'
        else:
            return ','.join(self)

    def prepare_to_store(self):
        return self.__str__()

def _converter(val, allowedElems, mapdict) -> _ListVariable:
    """ """
    if val == 'none':
        val = []
    elif val == 'all':
        val = allowedElems
    else:
        val = [_f for _f in val.split(',') if _f]
        val = [mapdict.get(v, v) for v in val]
        notAllowed = [v for v in val if v not in allowedElems]
        if notAllowed:
            raise ValueError(
                "Invalid value(s) for option: %s" % ','.join(notAllowed)
            )
    return _ListVariable(val, allowedElems)


# def _validator(key, val, env) -> None:
#     """ """
#     # TODO: write validator for pgk list
#     pass


def ListVariable(key, help, default, names, map={}) -> Tuple[str, str, str, None, Callable]:
    """Return a tuple describing a list SCons Variable.

    The input parameters describe a 'list' option. Returns
    a tuple including the correct converter and validator.
    The result is usable for input to :meth:`Add`.

    *help* will have text appended indicating the legal values
    (not including any extra names from *map*).

    *map* can be used to map alternative names to the ones in *names* -
    that is, a form of alias.

    A 'list' option may either be 'all', 'none' or a list of
    names (separated by commas).
    """
    names_str = 'allowed names: %s' % ' '.join(names)
    if SCons.Util.is_List(default):
        default = ','.join(default)
    help = '\n    '.join(
        (help, '(all|none|comma-separated list of names)', names_str))
    return (key, help, default, None, lambda val: _converter(val, names, map))

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
