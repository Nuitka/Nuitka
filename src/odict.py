# -*- coding: utf-8 -*-

# This module is only an abstraction and OrderedDict as present in 2.7 and 3.1
# but not in 2.6, there it is using the odict.py as mentioned in the PEP-0372
#
# This can be removed safely after the transition, not that the documentation
# was removed, as it's not interesting really, being redundent to Python 2.7
# documentation.

#    :copyright: (c) 2008 by Armin Ronacher and PEP 273 authors.
#    :license: modified BSD license.

# Kay Hayen did some changes for Nuitka, and put everything he added under the
# same modified BSD license.

try:
    from collections import OrderedDict
except ImportError:

    from itertools import izip, imap
    from copy import deepcopy

    missing = object()


    class odict(dict):
        def __init__(self, *args, **kwargs):
            dict.__init__(self)
            self._keys = []
            self.update(*args, **kwargs)

        def __delitem__(self, key):
            dict.__delitem__(self, key)
            self._keys.remove(key)

        def __setitem__(self, key, item):
            if key not in self:
                self._keys.append(key)
            dict.__setitem__(self, key, item)

        def __deepcopy__(self, memo=None):
            if memo is None:
                memo = {}
            d = memo.get(id(self), missing)
            if d is not missing:
                return d
            memo[id(self)] = d = self.__class__()
            dict.__init__(d, deepcopy(self.items(), memo))
            d._keys = self._keys[:]
            return d

        def __getstate__(self):
            return {'items': dict(self), 'keys': self._keys}

        def __setstate__(self, d):
            self._keys = d['keys']
            dict.update(d['items'])

        def __reversed__(self):
            return reversed(self._keys)

        def __eq__(self, other):
            if isinstance(other, odict):
                if not dict.__eq__(self, other):
                    return False
                return self.items() == other.items()
            return dict.__eq__(self, other)

        def __ne__(self, other):
            return not self.__eq__(other)

        def __cmp__(self, other):
            if isinstance(other, odict):
                return cmp(self.items(), other.items())
            elif isinstance(other, dict):
                return dict.__cmp__(self, other)
            return NotImplemented

        @classmethod
        def fromkeys(cls, iterable, default=None):
            return cls((key, default) for key in iterable)

        def clear(self):
            del self._keys[:]
            dict.clear(self)

        def copy(self):
            return self.__class__(self)

        def items(self):
            return zip(self._keys, self.values())

        def iteritems(self):
            return izip(self._keys, self.itervalues())

        def keys(self):
            return self._keys[:]

        def iterkeys(self):
            return iter(self._keys)

        def pop(self, key, default=missing):
            if default is missing:
                return dict.pop(self, key)
            elif key not in self:
                return default
            self._keys.remove(key)
            return dict.pop(self, key, default)

        def popitem(self, key):
            self._keys.remove(key)
            return dict.popitem(key)

        def setdefault(self, key, default=None):
            if key not in self:
                self._keys.append(key)
            dict.setdefault(self, key, default)

        def update(self, *args, **kwargs):
            sources = []
            if len(args) == 1:
                if hasattr(args[0], 'iteritems'):
                    sources.append(args[0].iteritems())
                else:
                    sources.append(iter(args[0]))
            elif args:
                raise TypeError('expected at most one positional argument')
            if kwargs:
                sources.append(kwargs.iteritems())
            for iterable in sources:
                for key, val in iterable:
                    self[key] = val

        def values(self):
            return map(self.get, self._keys)

        def itervalues(self):
            return imap(self.get, self._keys)

        def index(self, item):
            return self._keys.index(item)

        def byindex(self, item):
            key = self._keys[item]
            return (key, dict.__getitem__(self, key))

        def reverse(self):
            self._keys.reverse()

        def sort(self, *args, **kwargs):
            self._keys.sort(*args, **kwargs)

        def __repr__(self):
            return 'odict.odict(%r)' % self.items()

        __copy__ = copy
        __iter__ = iterkeys


    OrderedDict = odict
