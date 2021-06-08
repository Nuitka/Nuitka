# Copyright 2009 Raymond Hettinger
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Note: Kay Hayen did some changes for Nuitka keeping this license. These
# changes are not improvements, use the original source instead, not this
# file.

""" This module is only an abstraction of OrderedSet which is not present in
Python at all.

It was originally downloaded from http://code.activestate.com/recipes/576694/
"""

# pylint: disable=I0021,arguments-differ,redefined-builtin
from nuitka.__past__ import MutableSet

try:
    from orderedset import OrderedSet
except ImportError:

    class OrderedSet(MutableSet):
        def __init__(self, iterable=()):
            # pylint: disable=super-init-not-called

            self.end = end = []
            end += (None, end, end)  # sentinel node for doubly linked list
            self.map = {}  # key --> [key, prev, next]
            if iterable:
                self |= iterable

        def __len__(self):
            return len(self.map)

        def __contains__(self, key):
            return key in self.map

        def add(self, key):
            if key not in self.map:
                end = self.end
                curr = end[1]
                curr[2] = end[1] = self.map[key] = [key, curr, end]

        def update(self, keys):
            for key in keys:
                self.add(key)

        def discard(self, key):
            if key in self.map:
                key, prev, next = self.map.pop(key)
                prev[2] = next
                next[1] = prev

        def __iter__(self):
            end = self.end
            curr = end[2]
            while curr is not end:
                yield curr[0]
                curr = curr[2]

        def __reversed__(self):
            end = self.end
            curr = end[1]
            while curr is not end:
                yield curr[0]
                curr = curr[1]

        def pop(self, last=True):
            if not self:
                raise KeyError("set is empty")
            key = self.end[1][0] if last else self.end[2][0]
            self.discard(key)
            return key

        def __repr__(self):
            if not self:
                return "%s()" % (self.__class__.__name__,)
            return "%s(%r)" % (self.__class__.__name__, list(self))

        def __eq__(self, other):
            if isinstance(other, OrderedSet):
                return len(self) == len(other) and list(self) == list(other)
            return set(self) == set(other)

        def union(self, iterable):
            result = OrderedSet(self)

            for key in iterable:
                result.add(key)

            return result

        def index(self, key):
            if key in self.map:
                end = self.end
                curr = self.map[key]

                count = 0
                while curr is not end:
                    curr = curr[1]
                    count += 1

                return count - 1

            return None
