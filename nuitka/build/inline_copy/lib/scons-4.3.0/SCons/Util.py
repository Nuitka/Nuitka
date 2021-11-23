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

"""Various SCons utility functions."""

import copy
import hashlib
import os
import pprint
import re
import sys
from collections import UserDict, UserList, UserString, OrderedDict
from collections.abc import MappingView
from contextlib import suppress
from types import MethodType, FunctionType
from typing import Optional, Union

# Note: Util module cannot import other bits of SCons globally without getting
# into import loops. Both the below modules import SCons.Util early on.
# --> SCons.Warnings
# --> SCons.Errors
# Thus the local imports, which are annotated for pylint to show we mean it.


PYPY = hasattr(sys, 'pypy_translation_info')

# this string will be hashed if a Node refers to a file that doesn't exist
# in order to distinguish from a file that exists but is empty.
NOFILE = "SCONS_MAGIC_MISSING_FILE_STRING"

# unused?
def dictify(keys, values, result=None) -> dict:
    if result is None:
        result = {}
    result.update(dict(zip(keys, values)))
    return result

_ALTSEP = os.altsep
if _ALTSEP is None and sys.platform == 'win32':
    # My ActivePython 2.0.1 doesn't set os.altsep!  What gives?
    _ALTSEP = '/'
if _ALTSEP:
    def rightmost_separator(path, sep):
        return max(path.rfind(sep), path.rfind(_ALTSEP))
else:
    def rightmost_separator(path, sep):
        return path.rfind(sep)

# First two from the Python Cookbook, just for completeness.
# (Yeah, yeah, YAGNI...)
def containsAny(s, pat) -> bool:
    """Check whether string `s` contains ANY of the items in `pat`."""
    for c in pat:
        if c in s:
            return True
    return False

def containsAll(s, pat) -> bool:
    """Check whether string `s` contains ALL of the items in `pat`."""
    for c in pat:
        if c not in s:
            return False
    return True

def containsOnly(s, pat) -> bool:
    """Check whether string `s` contains ONLY items in `pat`."""
    for c in s:
        if c not in pat:
            return False
    return True


# TODO: Verify this method is STILL faster than os.path.splitext
def splitext(path) -> tuple:
    """Split `path` into a (root, ext) pair.

    Same as :mod:`os.path.splitext` but faster.
    """
    sep = rightmost_separator(path, os.sep)
    dot = path.rfind('.')
    # An ext is only real if it has at least one non-digit char
    if dot > sep and not containsOnly(path[dot:], "0123456789."):
        return path[:dot], path[dot:]

    return path, ""

def updrive(path) -> str:
    """Make the drive letter (if any) upper case.

    This is useful because Windows is inconsistent on the case
    of the drive letter, which can cause inconsistencies when
    calculating command signatures.
    """
    drive, rest = os.path.splitdrive(path)
    if drive:
        path = drive.upper() + rest
    return path

class NodeList(UserList):
    """A list of Nodes with special attribute retrieval.

    Unlike an ordinary list, access to a member's attribute returns a
    `NodeList` containing the same attribute for each member.  Although
    this can hold any object, it is intended for use when processing
    Nodes, where fetching an attribute of each member is very commone,
    for example getting the content signature of each node.  The term
    "attribute" here includes the string representation.

    Example:

    >>> someList = NodeList(['  foo  ', '  bar  '])
    >>> someList.strip()
    ['foo', 'bar']
    """

    def __bool__(self):
        return bool(self.data)

    def __str__(self):
        return ' '.join(map(str, self.data))

    def __iter__(self):
        return iter(self.data)

    def __call__(self, *args, **kwargs) -> 'NodeList':
        result = [x(*args, **kwargs) for x in self.data]
        return self.__class__(result)

    def __getattr__(self, name) -> 'NodeList':
        """Returns a NodeList of `name` from each member."""
        result = [getattr(x, name) for x in self.data]
        return self.__class__(result)

    def __getitem__(self, index):
        """Returns one item, forces a `NodeList` if `index` is a slice."""
        # TODO: annotate return how? Union[] - don't know type of single item
        if isinstance(index, slice):
            return self.__class__(self.data[index])
        return self.data[index]


_get_env_var = re.compile(r'^\$([_a-zA-Z]\w*|{[_a-zA-Z]\w*})$')

def get_environment_var(varstr) -> Optional[str]:
    """Return undecorated construction variable string.

    Determine if `varstr` looks like a reference
    to a single environment variable, like `"$FOO"` or `"${FOO}"`.
    If so, return that variable with no decorations, like `"FOO"`.
    If not, return `None`.
    """

    mo = _get_env_var.match(to_String(varstr))
    if mo:
        var = mo.group(1)
        if var[0] == '{':
            return var[1:-1]
        return var

    return None


class DisplayEngine:
    """A callable class used to display SCons messages."""

    print_it = True

    def __call__(self, text, append_newline=1):
        if not self.print_it:
            return

        if append_newline:
            text = text + '\n'

        try:
            sys.stdout.write(str(text))
        except IOError:
            # Stdout might be connected to a pipe that has been closed
            # by now. The most likely reason for the pipe being closed
            # is that the user has press ctrl-c. It this is the case,
            # then SCons is currently shutdown. We therefore ignore
            # IOError's here so that SCons can continue and shutdown
            # properly so that the .sconsign is correctly written
            # before SCons exits.
            pass

    def set_mode(self, mode):
        self.print_it = mode


# TODO: W0102: Dangerous default value [] as argument (dangerous-default-value)
def render_tree(root, child_func, prune=0, margin=[0], visited=None):
    """Render a tree of nodes into an ASCII tree view.

    Args:
        root: the root node of the tree
        child_func: the function called to get the children of a node
        prune: don't visit the same node twice
        margin: the format of the left margin to use for children of `root`.
          1 results in a pipe, and 0 results in no pipe.
        visited: a dictionary of visited nodes in the current branch if
          `prune` is 0, or in the whole tree if `prune` is 1.
    """

    rname = str(root)

    # Initialize 'visited' dict, if required
    if visited is None:
        visited = {}

    children = child_func(root)
    retval = ""
    for pipe in margin[:-1]:
        if pipe:
            retval = retval + "| "
        else:
            retval = retval + "  "

    if rname in visited:
        return retval + "+-[" + rname + "]\n"

    retval = retval + "+-" + rname + "\n"
    if not prune:
        visited = copy.copy(visited)
    visited[rname] = True

    for i, child in enumerate(children):
        margin.append(i < len(children)-1)
        retval = retval + render_tree(child, child_func, prune, margin, visited)
        margin.pop()

    return retval

def IDX(n) -> bool:
    """Generate in index into strings from the tree legends.

    These are always a choice between two, so bool works fine.
    """
    return bool(n)

# unicode line drawing chars:
BOX_HORIZ = chr(0x2500)  # '─'
BOX_VERT = chr(0x2502)  # '│'
BOX_UP_RIGHT = chr(0x2514)  # '└'
BOX_DOWN_RIGHT = chr(0x250c)  # '┌'
BOX_DOWN_LEFT = chr(0x2510)   # '┐'
BOX_UP_LEFT = chr(0x2518)  # '┘'
BOX_VERT_RIGHT = chr(0x251c)  # '├'
BOX_HORIZ_DOWN = chr(0x252c)  # '┬'


# TODO: W0102: Dangerous default value [] as argument (dangerous-default-value)
def print_tree(
    root,
    child_func,
    prune=0,
    showtags=False,
    margin=[0],
    visited=None,
    lastChild=False,
    singleLineDraw=False,
):
    """Print a tree of nodes.

    This is like func:`render_tree`, except it prints lines directly instead
    of creating a string representation in memory, so that huge trees can
    be handled.

    Args:
        root: the root node of the tree
        child_func: the function called to get the children of a node
        prune: don't visit the same node twice
        showtags: print status information to the left of each node line
        margin: the format of the left margin to use for children of `root`.
          1 results in a pipe, and 0 results in no pipe.
        visited: a dictionary of visited nodes in the current branch if
          prune` is 0, or in the whole tree if `prune` is 1.
        singleLineDraw: use line-drawing characters rather than ASCII.
    """

    rname = str(root)

    # Initialize 'visited' dict, if required
    if visited is None:
        visited = {}

    if showtags:

        if showtags == 2:
            legend = (' E         = exists\n' +
                      '  R        = exists in repository only\n' +
                      '   b       = implicit builder\n' +
                      '   B       = explicit builder\n' +
                      '    S      = side effect\n' +
                      '     P     = precious\n' +
                      '      A    = always build\n' +
                      '       C   = current\n' +
                      '        N  = no clean\n' +
                      '         H = no cache\n' +
                      '\n')
            sys.stdout.write(legend)

        tags = [
            '[',
            ' E'[IDX(root.exists())],
            ' R'[IDX(root.rexists() and not root.exists())],
            ' BbB'[
                [0, 1][IDX(root.has_explicit_builder())] +
                [0, 2][IDX(root.has_builder())]
            ],
            ' S'[IDX(root.side_effect)],
            ' P'[IDX(root.precious)],
            ' A'[IDX(root.always_build)],
            ' C'[IDX(root.is_up_to_date())],
            ' N'[IDX(root.noclean)],
            ' H'[IDX(root.nocache)],
            ']'
        ]

    else:
        tags = []

    def MMM(m):
        if singleLineDraw:
            return ["  ", BOX_VERT + " "][m]

        return ["  ", "| "][m]

    margins = list(map(MMM, margin[:-1]))
    children = child_func(root)
    cross = "+-"
    if singleLineDraw:
        cross = BOX_VERT_RIGHT + BOX_HORIZ   # sign used to point to the leaf.
        # check if this is the last leaf of the branch
        if lastChild:
            #if this if the last leaf, then terminate:
            cross = BOX_UP_RIGHT + BOX_HORIZ  # sign for the last leaf

        # if this branch has children then split it
        if children:
            # if it's a leaf:
            if prune and rname in visited and children:
                cross += BOX_HORIZ
            else:
                cross += BOX_HORIZ_DOWN

    if prune and rname in visited and children:
        sys.stdout.write(''.join(tags + margins + [cross,'[', rname, ']']) + '\n')
        return

    sys.stdout.write(''.join(tags + margins + [cross, rname]) + '\n')

    visited[rname] = 1

    # if this item has children:
    if children:
        margin.append(1)  # Initialize margin with 1 for vertical bar.
        idx = IDX(showtags)
        _child = 0  # Initialize this for the first child.
        for C in children[:-1]:
            _child = _child + 1  # number the children
            print_tree(
                C,
                child_func,
                prune,
                idx,
                margin,
                visited,
                (len(children) - _child) <= 0,
                singleLineDraw,
            )
        # margins are with space (index 0) because we arrived to the last child.
        margin[-1] = 0
        # for this call child and nr of children needs to be set 0, to signal the second phase.
        print_tree(children[-1], child_func, prune, idx, margin, visited, True, singleLineDraw)
        margin.pop()  # destroy the last margin added


# Functions for deciding if things are like various types, mainly to
# handle UserDict, UserList and UserString like their underlying types.
#
# Yes, all of this manual testing breaks polymorphism, and the real
# Pythonic way to do all of this would be to just try it and handle the
# exception, but handling the exception when it's not the right type is
# often too slow.

# We are using the following trick to speed up these
# functions. Default arguments are used to take a snapshot of
# the global functions and constants used by these functions. This
# transforms accesses to global variable into local variables
# accesses (i.e. LOAD_FAST instead of LOAD_GLOBAL).
# Since checkers dislike this, it's now annotated for pylint to flag
# (mostly for other readers of this code) we're doing this intentionally.
# TODO: PY3 check these are still valid choices for all of these funcs.

DictTypes = (dict, UserDict)
ListTypes = (list, UserList)

# Handle getting dictionary views.
SequenceTypes = (list, tuple, UserList, MappingView)

# Note that profiling data shows a speed-up when comparing
# explicitly with str instead of simply comparing
# with basestring. (at least on Python 2.5.1)
# TODO: PY3 check this benchmarking is still correct.
StringTypes = (str, UserString)

# Empirically, it is faster to check explicitly for str than for basestring.
BaseStringTypes = str

def is_Dict(  # pylint: disable=redefined-outer-name,redefined-builtin
    obj, isinstance=isinstance, DictTypes=DictTypes
) -> bool:
    return isinstance(obj, DictTypes)


def is_List(  # pylint: disable=redefined-outer-name,redefined-builtin
    obj, isinstance=isinstance, ListTypes=ListTypes
) -> bool:
    return isinstance(obj, ListTypes)


def is_Sequence(  # pylint: disable=redefined-outer-name,redefined-builtin
    obj, isinstance=isinstance, SequenceTypes=SequenceTypes
) -> bool:
    return isinstance(obj, SequenceTypes)


def is_Tuple(  # pylint: disable=redefined-builtin
    obj, isinstance=isinstance, tuple=tuple
) -> bool:
    return isinstance(obj, tuple)


def is_String(  # pylint: disable=redefined-outer-name,redefined-builtin
    obj, isinstance=isinstance, StringTypes=StringTypes
) -> bool:
    return isinstance(obj, StringTypes)


def is_Scalar(  # pylint: disable=redefined-outer-name,redefined-builtin
    obj, isinstance=isinstance, StringTypes=StringTypes, SequenceTypes=SequenceTypes
) -> bool:

    # Profiling shows that there is an impressive speed-up of 2x
    # when explicitly checking for strings instead of just not
    # sequence when the argument (i.e. obj) is already a string.
    # But, if obj is a not string then it is twice as fast to
    # check only for 'not sequence'. The following code therefore
    # assumes that the obj argument is a string most of the time.
    return isinstance(obj, StringTypes) or not isinstance(obj, SequenceTypes)


def do_flatten(
    sequence,
    result,
    isinstance=isinstance,
    StringTypes=StringTypes,
    SequenceTypes=SequenceTypes,
):  # pylint: disable=redefined-outer-name,redefined-builtin
    for item in sequence:
        if isinstance(item, StringTypes) or not isinstance(item, SequenceTypes):
            result.append(item)
        else:
            do_flatten(item, result)


def flatten(  # pylint: disable=redefined-outer-name,redefined-builtin
    obj,
    isinstance=isinstance,
    StringTypes=StringTypes,
    SequenceTypes=SequenceTypes,
    do_flatten=do_flatten,
) -> list:
    """Flatten a sequence to a non-nested list.

    Converts either a single scalar or a nested sequence to a non-nested list.
    Note that :func:`flatten` considers strings
    to be scalars instead of sequences like pure Python would.
    """
    if isinstance(obj, StringTypes) or not isinstance(obj, SequenceTypes):
        return [obj]
    result = []
    for item in obj:
        if isinstance(item, StringTypes) or not isinstance(item, SequenceTypes):
            result.append(item)
        else:
            do_flatten(item, result)
    return result


def flatten_sequence(  # pylint: disable=redefined-outer-name,redefined-builtin
    sequence,
    isinstance=isinstance,
    StringTypes=StringTypes,
    SequenceTypes=SequenceTypes,
    do_flatten=do_flatten,
) -> list:
    """Flatten a sequence to a non-nested list.

    Same as :func:`flatten`, but it does not handle the single scalar case.
    This is slightly more efficient when one knows that the sequence
    to flatten can not be a scalar.
    """
    result = []
    for item in sequence:
        if isinstance(item, StringTypes) or not isinstance(item, SequenceTypes):
            result.append(item)
        else:
            do_flatten(item, result)
    return result

# Generic convert-to-string functions.  The wrapper
# to_String_for_signature() will use a for_signature() method if the
# specified object has one.

def to_String(  # pylint: disable=redefined-outer-name,redefined-builtin
    obj,
    isinstance=isinstance,
    str=str,
    UserString=UserString,
    BaseStringTypes=BaseStringTypes,
) -> str:
    """Return a string version of obj."""

    if isinstance(obj, BaseStringTypes):
        # Early out when already a string!
        return obj

    if isinstance(obj, UserString):
        # obj.data can only be a regular string. Please see the UserString initializer.
        return obj.data

    return str(obj)

def to_String_for_subst(  # pylint: disable=redefined-outer-name,redefined-builtin
    obj,
    isinstance=isinstance,
    str=str,
    BaseStringTypes=BaseStringTypes,
    SequenceTypes=SequenceTypes,
    UserString=UserString,
) -> str:
    """Return a string version of obj for subst usage."""

    # Note that the test cases are sorted by order of probability.
    if isinstance(obj, BaseStringTypes):
        return obj

    if isinstance(obj, SequenceTypes):
        return ' '.join([to_String_for_subst(e) for e in obj])

    if isinstance(obj, UserString):
        # obj.data can only a regular string. Please see the UserString initializer.
        return obj.data

    return str(obj)

def to_String_for_signature(  # pylint: disable=redefined-outer-name,redefined-builtin
    obj, to_String_for_subst=to_String_for_subst, AttributeError=AttributeError
) -> str:
    """Return a string version of obj for signature usage.

    Like :func:`to_String_for_subst` but has special handling for
    scons objects that have a :meth:`for_signature` method, and for dicts.
    """

    try:
        f = obj.for_signature
    except AttributeError:
        if isinstance(obj, dict):
            # pprint will output dictionary in key sorted order
            # with py3.5 the order was randomized. In general depending on dictionary order
            # which was undefined until py3.6 (where it's by insertion order) was not wise.
            # TODO: Change code when floor is raised to PY36
            return pprint.pformat(obj, width=1000000)
        return to_String_for_subst(obj)
    else:
        return f()


# The SCons "semi-deep" copy.
#
# This makes separate copies of lists (including UserList objects)
# dictionaries (including UserDict objects) and tuples, but just copies
# references to anything else it finds.
#
# A special case is any object that has a __semi_deepcopy__() method,
# which we invoke to create the copy. Currently only used by
# BuilderDict to actually prevent the copy operation (as invalid on that object).
#
# The dispatch table approach used here is a direct rip-off from the
# normal Python copy module.

def semi_deepcopy_dict(obj, exclude=None) -> dict:
    if exclude is None:
        exclude = []
    return {k: semi_deepcopy(v) for k, v in obj.items() if k not in exclude}

def _semi_deepcopy_list(obj) -> list:
    return [semi_deepcopy(item) for item in obj]

def _semi_deepcopy_tuple(obj) -> tuple:
    return tuple(map(semi_deepcopy, obj))

_semi_deepcopy_dispatch = {
    dict: semi_deepcopy_dict,
    list: _semi_deepcopy_list,
    tuple: _semi_deepcopy_tuple,
}

def semi_deepcopy(obj):
    copier = _semi_deepcopy_dispatch.get(type(obj))
    if copier:
        return copier(obj)

    if hasattr(obj, '__semi_deepcopy__') and callable(obj.__semi_deepcopy__):
        return obj.__semi_deepcopy__()

    if isinstance(obj, UserDict):
        return obj.__class__(semi_deepcopy_dict(obj))

    if isinstance(obj, UserList):
        return obj.__class__(_semi_deepcopy_list(obj))

    return obj


class Proxy:
    """A simple generic Proxy class, forwarding all calls to subject.

    This means you can take an object, let's call it `'obj_a`,
    and wrap it in this Proxy class, with a statement like this::

        proxy_obj = Proxy(obj_a)

    Then, if in the future, you do something like this::

        x = proxy_obj.var1

    since the :class:`Proxy` class does not have a :attr:`var1` attribute
    (but presumably `objA` does), the request actually is equivalent to saying::

        x = obj_a.var1

    Inherit from this class to create a Proxy.

    With Python 3.5+ this does *not* work transparently
    for :class:`Proxy` subclasses that use special .__*__() method names,
    because those names are now bound to the class, not the individual
    instances.  You now need to know in advance which special method names you
    want to pass on to the underlying Proxy object, and specifically delegate
    their calls like this::

        class Foo(Proxy):
            __str__ = Delegate('__str__')
    """

    def __init__(self, subject):
        """Wrap an object as a Proxy object"""
        self._subject = subject

    def __getattr__(self, name):
        """Retrieve an attribute from the wrapped object.

        Raises:
           AttributeError: if attribute `name` doesn't exist.
        """
        return getattr(self._subject, name)

    def get(self):
        """Retrieve the entire wrapped object"""
        return self._subject

    def __eq__(self, other):
        if issubclass(other.__class__, self._subject.__class__):
            return self._subject == other
        return self.__dict__ == other.__dict__


class Delegate:
    """A Python Descriptor class that delegates attribute fetches
    to an underlying wrapped subject of a Proxy.  Typical use::

        class Foo(Proxy):
            __str__ = Delegate('__str__')
    """
    def __init__(self, attribute):
        self.attribute = attribute

    def __get__(self, obj, cls):
        if isinstance(obj, cls):
            return getattr(obj._subject, self.attribute)

        return self


class MethodWrapper:
    """A generic Wrapper class that associates a method with an object.

    As part of creating this MethodWrapper object an attribute with the
    specified name (by default, the name of the supplied method) is added
    to the underlying object.  When that new "method" is called, our
    :meth:`__call__` method adds the object as the first argument, simulating
    the Python behavior of supplying "self" on method calls.

    We hang on to the name by which the method was added to the underlying
    base class so that we can provide a method to "clone" ourselves onto
    a new underlying object being copied (without which we wouldn't need
    to save that info).
    """
    def __init__(self, obj, method, name=None):
        if name is None:
            name = method.__name__
        self.object = obj
        self.method = method
        self.name = name
        setattr(self.object, name, self)

    def __call__(self, *args, **kwargs):
        nargs = (self.object,) + args
        return self.method(*nargs, **kwargs)

    def clone(self, new_object):
        """
        Returns an object that re-binds the underlying "method" to
        the specified new object.
        """
        return self.__class__(new_object, self.method, self.name)


# attempt to load the windows registry module:
can_read_reg = False
try:
    import winreg

    can_read_reg = True
    hkey_mod = winreg

except ImportError:
    class _NoError(Exception):
        pass
    RegError = _NoError

if can_read_reg:
    HKEY_CLASSES_ROOT = hkey_mod.HKEY_CLASSES_ROOT
    HKEY_LOCAL_MACHINE = hkey_mod.HKEY_LOCAL_MACHINE
    HKEY_CURRENT_USER = hkey_mod.HKEY_CURRENT_USER
    HKEY_USERS = hkey_mod.HKEY_USERS

    RegOpenKeyEx = winreg.OpenKeyEx
    RegEnumKey = winreg.EnumKey
    RegEnumValue = winreg.EnumValue
    RegQueryValueEx = winreg.QueryValueEx
    RegError = winreg.error

    def RegGetValue(root, key):
        r"""Returns a registry value without having to open the key first.

        Only available on Windows platforms with a version of Python that
        can read the registry.

        Returns the same thing as :func:`RegQueryValueEx`, except you just
        specify the entire path to the value, and don't have to bother
        opening the key first.  So, instead of::

          k = SCons.Util.RegOpenKeyEx(SCons.Util.HKEY_LOCAL_MACHINE,
                r'SOFTWARE\Microsoft\Windows\CurrentVersion')
          out = SCons.Util.RegQueryValueEx(k, 'ProgramFilesDir')

        You can write::

          out = SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE,
                r'SOFTWARE\Microsoft\Windows\CurrentVersion\ProgramFilesDir')
        """
        # I would use os.path.split here, but it's not a filesystem
        # path...
        p = key.rfind('\\') + 1
        keyp = key[: p - 1]  # -1 to omit trailing slash
        val = key[p:]
        k = RegOpenKeyEx(root, keyp)
        return RegQueryValueEx(k, val)


else:
    HKEY_CLASSES_ROOT = None
    HKEY_LOCAL_MACHINE = None
    HKEY_CURRENT_USER = None
    HKEY_USERS = None

    def RegGetValue(root, key):
        raise OSError

    def RegOpenKeyEx(root, key):
        raise OSError


if sys.platform == 'win32':

    def WhereIs(file, path=None, pathext=None, reject=None) -> Optional[str]:
        if path is None:
            try:
                path = os.environ['PATH']
            except KeyError:
                return None
        if is_String(path):
            path = path.split(os.pathsep)
        if pathext is None:
            try:
                pathext = os.environ['PATHEXT']
            except KeyError:
                pathext = '.COM;.EXE;.BAT;.CMD'
        if is_String(pathext):
            pathext = pathext.split(os.pathsep)
        for ext in pathext:
            if ext.lower() == file[-len(ext):].lower():
                pathext = ['']
                break
        if reject is None:
            reject = []
        if not is_List(reject) and not is_Tuple(reject):
            reject = [reject]
        for p in path:
            f = os.path.join(p, file)
            for ext in pathext:
                fext = f + ext
                if os.path.isfile(fext):
                    try:
                        reject.index(fext)
                    except ValueError:
                        return os.path.normpath(fext)
                    continue
        return None

elif os.name == 'os2':

    def WhereIs(file, path=None, pathext=None, reject=None) -> Optional[str]:
        if path is None:
            try:
                path = os.environ['PATH']
            except KeyError:
                return None
        if is_String(path):
            path = path.split(os.pathsep)
        if pathext is None:
            pathext = ['.exe', '.cmd']
        for ext in pathext:
            if ext.lower() == file[-len(ext):].lower():
                pathext = ['']
                break
        if reject is None:
            reject = []
        if not is_List(reject) and not is_Tuple(reject):
            reject = [reject]
        for p in path:
            f = os.path.join(p, file)
            for ext in pathext:
                fext = f + ext
                if os.path.isfile(fext):
                    try:
                        reject.index(fext)
                    except ValueError:
                        return os.path.normpath(fext)
                    continue
        return None

else:

    def WhereIs(file, path=None, pathext=None, reject=None) -> Optional[str]:
        import stat  # pylint: disable=import-outside-toplevel

        if path is None:
            try:
                path = os.environ['PATH']
            except KeyError:
                return None
        if is_String(path):
            path = path.split(os.pathsep)
        if reject is None:
            reject = []
        if not is_List(reject) and not is_Tuple(reject):
            reject = [reject]
        for p in path:
            f = os.path.join(p, file)
            if os.path.isfile(f):
                try:
                    st = os.stat(f)
                except OSError:
                    # os.stat() raises OSError, not IOError if the file
                    # doesn't exist, so in this case we let IOError get
                    # raised so as to not mask possibly serious disk or
                    # network issues.
                    continue
                if stat.S_IMODE(st[stat.ST_MODE]) & 0o111:
                    try:
                        reject.index(f)
                    except ValueError:
                        return os.path.normpath(f)
                    continue
        return None

WhereIs.__doc__ = """\
Return the path to an executable that matches `file`.

Searches the given `path` for `file`, respecting any filename
extensions `pathext` (on the Windows platform only), and
returns the full path to the matching command.  If no
command is found, return ``None``.

If `path` is not specified, :attr:`os.environ[PATH]` is used.
If `pathext` is not specified, :attr:`os.environ[PATHEXT]`
is used. Will not select any path name or names in the optional
`reject` list.
"""

def PrependPath(
    oldpath, newpath, sep=os.pathsep, delete_existing=True, canonicalize=None
) -> Union[list, str]:
    """Prepends `newpath` path elements to `oldpath`.

    Will only add any particular path once (leaving the first one it
    encounters and ignoring the rest, to preserve path order), and will
    :mod:`os.path.normpath` and :mod:`os.path.normcase` all paths to help
    assure this.  This can also handle the case where `oldpath`
    is a list instead of a string, in which case a list will be returned
    instead of a string. For example:

    >>> p = PrependPath("/foo/bar:/foo", "/biz/boom:/foo")
    >>> print(p)
    /biz/boom:/foo:/foo/bar

    If `delete_existing` is ``False``, then adding a path that exists will
    not move it to the beginning; it will stay where it is in the list.

    >>> p = PrependPath("/foo/bar:/foo", "/biz/boom:/foo", delete_existing=False)
    >>> print(p)
    /biz/boom:/foo/bar:/foo

    If `canonicalize` is not ``None``, it is applied to each element of
    `newpath` before use.
    """

    orig = oldpath
    is_list = True
    paths = orig
    if not is_List(orig) and not is_Tuple(orig):
        paths = paths.split(sep)
        is_list = False

    if is_String(newpath):
        newpaths = newpath.split(sep)
    elif not is_List(newpath) and not is_Tuple(newpath):
        newpaths = [ newpath ]  # might be a Dir
    else:
        newpaths = newpath

    if canonicalize:
        newpaths=list(map(canonicalize, newpaths))

    if not delete_existing:
        # First uniquify the old paths, making sure to
        # preserve the first instance (in Unix/Linux,
        # the first one wins), and remembering them in normpaths.
        # Then insert the new paths at the head of the list
        # if they're not already in the normpaths list.
        result = []
        normpaths = []
        for path in paths:
            if not path:
                continue
            normpath = os.path.normpath(os.path.normcase(path))
            if normpath not in normpaths:
                result.append(path)
                normpaths.append(normpath)
        newpaths.reverse()      # since we're inserting at the head
        for path in newpaths:
            if not path:
                continue
            normpath = os.path.normpath(os.path.normcase(path))
            if normpath not in normpaths:
                result.insert(0, path)
                normpaths.append(normpath)
        paths = result

    else:
        newpaths = newpaths + paths # prepend new paths

        normpaths = []
        paths = []
        # now we add them only if they are unique
        for path in newpaths:
            normpath = os.path.normpath(os.path.normcase(path))
            if path and normpath not in normpaths:
                paths.append(path)
                normpaths.append(normpath)

    if is_list:
        return paths

    return sep.join(paths)

def AppendPath(
    oldpath, newpath, sep=os.pathsep, delete_existing=True, canonicalize=None
) -> Union[list, str]:
    """Appends `newpath` path elements to `oldpath`.

    Will only add any particular path once (leaving the last one it
    encounters and ignoring the rest, to preserve path order), and will
    :mod:`os.path.normpath` and :mod:`os.path.normcase` all paths to help
    assure this.  This can also handle the case where `oldpath`
    is a list instead of a string, in which case a list will be returned
    instead of a string. For example:

    >>> p = AppendPath("/foo/bar:/foo", "/biz/boom:/foo")
    >>> print(p)
    /foo/bar:/biz/boom:/foo

    If `delete_existing` is ``False``, then adding a path that exists
    will not move it to the end; it will stay where it is in the list.

    >>> p = AppendPath("/foo/bar:/foo", "/biz/boom:/foo", delete_existing=False)
    >>> print(p)
    /foo/bar:/foo:/biz/boom

    If `canonicalize` is not ``None``, it is applied to each element of
    `newpath` before use.
    """

    orig = oldpath
    is_list = True
    paths = orig
    if not is_List(orig) and not is_Tuple(orig):
        paths = paths.split(sep)
        is_list = False

    if is_String(newpath):
        newpaths = newpath.split(sep)
    elif not is_List(newpath) and not is_Tuple(newpath):
        newpaths = [newpath]  # might be a Dir
    else:
        newpaths = newpath

    if canonicalize:
        newpaths=list(map(canonicalize, newpaths))

    if not delete_existing:
        # add old paths to result, then
        # add new paths if not already present
        # (I thought about using a dict for normpaths for speed,
        # but it's not clear hashing the strings would be faster
        # than linear searching these typically short lists.)
        result = []
        normpaths = []
        for path in paths:
            if not path:
                continue
            result.append(path)
            normpaths.append(os.path.normpath(os.path.normcase(path)))
        for path in newpaths:
            if not path:
                continue
            normpath = os.path.normpath(os.path.normcase(path))
            if normpath not in normpaths:
                result.append(path)
                normpaths.append(normpath)
        paths = result
    else:
        # start w/ new paths, add old ones if not present,
        # then reverse.
        newpaths = paths + newpaths # append new paths
        newpaths.reverse()

        normpaths = []
        paths = []
        # now we add them only if they are unique
        for path in newpaths:
            normpath = os.path.normpath(os.path.normcase(path))
            if path and normpath not in normpaths:
                paths.append(path)
                normpaths.append(normpath)
        paths.reverse()

    if is_list:
        return paths

    return sep.join(paths)

def AddPathIfNotExists(env_dict, key, path, sep=os.pathsep):
    """Add a path element to a construction variable.

    `key` is looked up in `env_dict`, and `path` is added to it if it
    is not already present. `env_dict[key]` is assumed to be in the
    format of a PATH variable: a list of paths separated by `sep` tokens.
    Example:

    >>> env = {'PATH': '/bin:/usr/bin:/usr/local/bin'}
    >>> AddPathIfNotExists(env, 'PATH', '/opt/bin')
    >>> print(env['PATH'])
    /opt/bin:/bin:/usr/bin:/usr/local/bin
    """

    try:
        is_list = True
        paths = env_dict[key]
        if not is_List(env_dict[key]):
            paths = paths.split(sep)
            is_list = False
        if os.path.normcase(path) not in list(map(os.path.normcase, paths)):
            paths = [ path ] + paths
        if is_list:
            env_dict[key] = paths
        else:
            env_dict[key] = sep.join(paths)
    except KeyError:
        env_dict[key] = path

if sys.platform == 'cygwin':
    import subprocess  # pylint: disable=import-outside-toplevel

    def get_native_path(path) -> str:
        cp = subprocess.run(('cygpath', '-w', path), check=False, stdout=subprocess.PIPE)
        return cp.stdout.decode().replace('\n', '')
else:
    def get_native_path(path) -> str:
        return path

get_native_path.__doc__ = """\
Transform an absolute path into a native path for the system.

In Cygwin, this converts from a Cygwin path to a Windows path,
without regard to whether `path` refers to an existing file
system object.  For other platforms, `path` is unchanged.
"""


display = DisplayEngine()

def Split(arg) -> list:
    """Returns a list of file names or other objects.

    If `arg` is a string, it will be split on strings of white-space
    characters within the string.  If `arg` is already a list, the list
    will be returned untouched. If `arg` is any other type of object,
    it will be returned as a list containing just the object.

    >>> print(Split(" this  is  a  string  "))
    ['this', 'is', 'a', 'string']
    >>> print(Split(["stringlist", " preserving ", " spaces "]))
    ['stringlist', ' preserving ', ' spaces ']
    """
    if is_List(arg) or is_Tuple(arg):
        return arg

    if is_String(arg):
        return arg.split()

    return [arg]


class CLVar(UserList):
    """A container for command-line construction variables.

    Forces the use of a list of strings intended as command-line
    arguments.  Like :class:`collections.UserList`, but the argument
    passed to the initializter will be processed by the :func:`Split`
    function, which includes special handling for string types: they
    will be split into a list of words, not coereced directly to a list.
    The same happens if a string is added to a :class:`CLVar`,
    which allows doing the right thing with both
    :func:`Append`/:func:`Prepend` methods,
    as well as with pure Python addition, regardless of whether adding
    a list or a string to a construction variable.

    Side effect: spaces will be stripped from individual string
    arguments. If you need spaces preserved, pass strings containing
    spaces inside a list argument.

    >>> u = UserList("--some --opts and args")
    >>> print(len(u), repr(u))
    22 ['-', '-', 's', 'o', 'm', 'e', ' ', '-', '-', 'o', 'p', 't', 's', ' ', 'a', 'n', 'd', ' ', 'a', 'r', 'g', 's']
    >>> c = CLVar("--some --opts and args")
    >>> print(len(c), repr(c))
    4 ['--some', '--opts', 'and', 'args']
    >>> c += "    strips spaces    "
    >>> print(len(c), repr(c))
    6 ['--some', '--opts', 'and', 'args', 'strips', 'spaces']
    """

    def __init__(self, initlist=None):
        super().__init__(Split(initlist if initlist is not None else []))

    def __add__(self, other):
        return super().__add__(CLVar(other))

    def __radd__(self, other):
        return super().__radd__(CLVar(other))

    def __iadd__(self, other):
        return super().__iadd__(CLVar(other))

    def __str__(self):
        return ' '.join(self.data)


class Selector(OrderedDict):
    """A callable ordered dictionary that maps file suffixes to
    dictionary values.  We preserve the order in which items are added
    so that :func:`get_suffix` calls always return the first suffix added.
    """
    def __call__(self, env, source, ext=None):
        if ext is None:
            try:
                ext = source[0].get_suffix()
            except IndexError:
                ext = ""
        try:
            return self[ext]
        except KeyError:
            # Try to perform Environment substitution on the keys of
            # the dictionary before giving up.
            s_dict = {}
            for (k,v) in self.items():
                if k is not None:
                    s_k = env.subst(k)
                    if s_k in s_dict:
                        # We only raise an error when variables point
                        # to the same suffix.  If one suffix is literal
                        # and a variable suffix contains this literal,
                        # the literal wins and we don't raise an error.
                        raise KeyError(s_dict[s_k][0], k, s_k)
                    s_dict[s_k] = (k,v)
            try:
                return s_dict[ext][1]
            except KeyError:
                try:
                    return self[None]
                except KeyError:
                    return None


if sys.platform == 'cygwin':
    # On Cygwin, os.path.normcase() lies, so just report back the
    # fact that the underlying Windows OS is case-insensitive.
    def case_sensitive_suffixes(s1, s2) -> bool:  # pylint: disable=unused-argument
        return False

else:
    def case_sensitive_suffixes(s1, s2) -> bool:
        return os.path.normcase(s1) != os.path.normcase(s2)


def adjustixes(fname, pre, suf, ensure_suffix=False) -> str:
    """Adjust filename prefixes and suffixes as needed.

    Add `prefix` to `fname` if specified.
    Add `suffix` to `fname` if specified and if `ensure_suffix` is ``True``
    """

    if pre:
        path, fn = os.path.split(os.path.normpath(fname))

        # Handle the odd case where the filename = the prefix.
        # In that case, we still want to add the prefix to the file
        if not fn.startswith(pre) or fn == pre:
            fname = os.path.join(path, pre + fn)
    # Only append a suffix if the suffix we're going to add isn't already
    # there, and if either we've been asked to ensure the specific suffix
    # is present or there's no suffix on it at all.
    # Also handle the odd case where the filename = the suffix.
    # in that case we still want to append the suffix
    if suf and not fname.endswith(suf) and \
            (ensure_suffix or not splitext(fname)[1]):
        fname = fname + suf
    return fname



# From Tim Peters,
# https://code.activestate.com/recipes/52560
# ASPN: Python Cookbook: Remove duplicates from a sequence
# (Also in the printed Python Cookbook.)
# Updated. This algorithm is used by some scanners and tools.

def unique(seq):
    """Return a list of the elements in seq without duplicates, ignoring order.

    >>> mylist = unique([1, 2, 3, 1, 2, 3])
    >>> print(sorted(mylist))
    [1, 2, 3]
    >>> mylist = unique("abcabc")
    >>> print(sorted(mylist))
    ['a', 'b', 'c']
    >>> mylist = unique(([1, 2], [2, 3], [1, 2]))
    >>> print(sorted(mylist))
    [[1, 2], [2, 3]]

    For best speed, all sequence elements should be hashable.  Then
    unique() will usually work in linear time.

    If not possible, the sequence elements should enjoy a total
    ordering, and if list(s).sort() doesn't raise TypeError it's
    assumed that they do enjoy a total ordering.  Then unique() will
    usually work in O(N*log2(N)) time.

    If that's not possible either, the sequence elements must support
    equality-testing.  Then unique() will usually work in quadratic time.
    """

    if not seq:
        return []

    # Try using a dict first, as that's the fastest and will usually
    # work.  If it doesn't work, it will usually fail quickly, so it
    # usually doesn't cost much to *try* it.  It requires that all the
    # sequence elements be hashable, and support equality comparison.
    # TODO: should be even faster: return(list(set(seq)))
    with suppress(TypeError):
        return list(dict.fromkeys(seq))

    # We couldn't hash all the elements (got a TypeError).
    # Next fastest is to sort, which brings the equal elements together;
    # then duplicates are easy to weed out in a single pass.
    # NOTE:  Python's list.sort() was designed to be efficient in the
    # presence of many duplicate elements.  This isn't true of all
    # sort functions in all languages or libraries, so this approach
    # is more effective in Python than it may be elsewhere.
    n = len(seq)
    try:
        t = sorted(seq)
    except TypeError:
        pass    # move on to the next method
    else:
        last = t[0]
        lasti = i = 1
        while i < n:
            if t[i] != last:
                t[lasti] = last = t[i]
                lasti = lasti + 1
            i = i + 1
        return t[:lasti]

    # Brute force is all that's left.
    u = []
    for x in seq:
        if x not in u:
            u.append(x)
    return u


# From Alex Martelli,
# https://code.activestate.com/recipes/52560
# ASPN: Python Cookbook: Remove duplicates from a sequence
# First comment, dated 2001/10/13.
# (Also in the printed Python Cookbook.)
# This not currently used, in favor of the next function...

def uniquer(seq, idfun=None):
    def default_idfun(x):
        return x
    if not idfun:
        idfun = default_idfun
    seen = {}
    result = []
    result_append = result.append  # perf: avoid repeated method lookups
    for item in seq:
        marker = idfun(item)
        if marker in seen:
            continue
        seen[marker] = 1
        result_append(item)
    return result

# A more efficient implementation of Alex's uniquer(), this avoids the
# idfun() argument and function-call overhead by assuming that all
# items in the sequence are hashable.  Order-preserving.

def uniquer_hashables(seq):
    seen = {}
    result = []
    result_append = result.append  # perf: avoid repeated method lookups
    for item in seq:
        if item not in seen:
            seen[item] = 1
            result_append(item)
    return result


# Recipe 19.11 "Reading Lines with Continuation Characters",
# by Alex Martelli, straight from the Python CookBook (2nd edition).
def logical_lines(physical_lines, joiner=''.join):
    logical_line = []
    for line in physical_lines:
        stripped = line.rstrip()
        if stripped.endswith('\\'):
            # a line which continues w/the next physical line
            logical_line.append(stripped[:-1])
        else:
            # a line which does not continue, end of logical line
            logical_line.append(line)
            yield joiner(logical_line)
            logical_line = []
    if logical_line:
        # end of sequence implies end of last logical line
        yield joiner(logical_line)


class LogicalLines:
    """ Wrapper class for the logical_lines method.

    Allows us to read all "logical" lines at once from a given file object.
    """

    def __init__(self, fileobj):
        self.fileobj = fileobj

    def readlines(self):
        return list(logical_lines(self.fileobj))


class UniqueList(UserList):
    """A list which maintains uniqueness.

    Uniquing is lazy: rather than being assured on list changes, it is fixed
    up on access by those methods which need to act on a uniqe list to be
    correct. That means things like "in" don't have to eat the uniquing time.
    """
    def __init__(self, initlist=None):
        super().__init__(initlist)
        self.unique = True

    def __make_unique(self):
        if not self.unique:
            self.data = uniquer_hashables(self.data)
            self.unique = True

    def __repr__(self):
        self.__make_unique()
        return super().__repr__()

    def __lt__(self, other):
        self.__make_unique()
        return super().__lt__(other)

    def __le__(self, other):
        self.__make_unique()
        return super().__le__(other)

    def __eq__(self, other):
        self.__make_unique()
        return super().__eq__(other)

    def __ne__(self, other):
        self.__make_unique()
        return super().__ne__(other)

    def __gt__(self, other):
        self.__make_unique()
        return super().__gt__(other)

    def __ge__(self, other):
        self.__make_unique()
        return super().__ge__(other)

    # __contains__ doesn't need to worry about uniquing, inherit

    def __len__(self):
        self.__make_unique()
        return super().__len__()

    def __getitem__(self, i):
        self.__make_unique()
        return super().__getitem__(i)

    def __setitem__(self, i, item):
        super().__setitem__(i, item)
        self.unique = False

    # __delitem__ doesn't need to worry about uniquing, inherit

    def __add__(self, other):
        result = super().__add__(other)
        result.unique = False
        return result

    def __radd__(self, other):
        result = super().__radd__(other)
        result.unique = False
        return result

    def __iadd__(self, other):
        result = super().__iadd__(other)
        result.unique = False
        return result

    def __mul__(self, other):
        result = super().__mul__(other)
        result.unique = False
        return result

    def __rmul__(self, other):
        result = super().__rmul__(other)
        result.unique = False
        return result

    def __imul__(self, other):
        result = super().__imul__(other)
        result.unique = False
        return result

    def append(self, item):
        super().append(item)
        self.unique = False

    def insert(self, i, item):
        super().insert(i, item)
        self.unique = False

    def count(self, item):
        self.__make_unique()
        return super().count(item)

    def index(self, item, *args):
        self.__make_unique()
        return super().index(item, *args)

    def reverse(self):
        self.__make_unique()
        super().reverse()

    # TODO: Py3.8: def sort(self, /, *args, **kwds):
    def sort(self, *args, **kwds):
        self.__make_unique()
        return super().sort(*args, **kwds)

    def extend(self, other):
        super().extend(other)
        self.unique = False


class Unbuffered:
    """A proxy  that wraps a file object, flushing after every write.

    Delegates everything else to the wrapped object.
    """
    def __init__(self, file):
        self.file = file

    def write(self, arg):
        # Stdout might be connected to a pipe that has been closed
        # by now. The most likely reason for the pipe being closed
        # is that the user has press ctrl-c. It this is the case,
        # then SCons is currently shutdown. We therefore ignore
        # IOError's here so that SCons can continue and shutdown
        # properly so that the .sconsign is correctly written
        # before SCons exits.
        with suppress(IOError):
            self.file.write(arg)
            self.file.flush()

    def writelines(self, arg):
        with suppress(IOError):
            self.file.writelines(arg)
            self.file.flush()

    def __getattr__(self, attr):
        return getattr(self.file, attr)

def make_path_relative(path) -> str:
    """Converts an absolute path name to a relative pathname."""

    if os.path.isabs(path):
        drive_s, path = os.path.splitdrive(path)

        if not drive_s:
            path=re.compile(r"/*(.*)").findall(path)[0]
        else:
            path=path[1:]

    assert not os.path.isabs(path), path
    return path


# The original idea for AddMethod() came from the
# following post to the ActiveState Python Cookbook:
#
# ASPN: Python Cookbook : Install bound methods in an instance
# https://code.activestate.com/recipes/223613
#
# Changed as follows:
# * Switched the installmethod() "object" and "function" arguments,
#   so the order reflects that the left-hand side is the thing being
#   "assigned to" and the right-hand side is the value being assigned.
# * The instance/class detection is changed a bit, as it's all
#   new-style classes now with Py3.
# * The by-hand construction of the function object from renamefunction()
#   is not needed, the remaining bit is now used inline in AddMethod.

def AddMethod(obj, function, name=None):
    """Adds a method to an object.

    Adds `function` to `obj` if `obj` is a class object.
    Adds `function` as a bound method if `obj` is an instance object.
    If `obj` looks like an environment instance, use `MethodWrapper`
    to add it.  If `name` is supplied it is used as the name of `function`.

    Although this works for any class object, the intent as a public
    API is to be used on Environment, to be able to add a method to all
    construction environments; it is preferred to use env.AddMethod
    to add to an individual environment.

    >>> class A:
    ...    ...

    >>> a = A()

    >>> def f(self, x, y):
    ...    self.z = x + y

    >>> AddMethod(A, f, "add")
    >>> a.add(2, 4)
    >>> print(a.z)
    6
    >>> a.data = ['a', 'b', 'c', 'd', 'e', 'f']
    >>> AddMethod(a, lambda self, i: self.data[i], "listIndex")
    >>> print(a.listIndex(3))
    d

    """
    if name is None:
        name = function.__name__
    else:
        # "rename"
        function = FunctionType(
            function.__code__, function.__globals__, name, function.__defaults__
        )

    if hasattr(obj, '__class__') and obj.__class__ is not type:
        # obj is an instance, so it gets a bound method.
        if hasattr(obj, "added_methods"):
            method = MethodWrapper(obj, function, name)
            obj.added_methods.append(method)
        else:
            method = MethodType(function, obj)
    else:
        # obj is a class
        method = function

    setattr(obj, name, method)


# Default hash function and format. SCons-internal.
DEFAULT_HASH_FORMATS = ['md5', 'sha1', 'sha256']
ALLOWED_HASH_FORMATS = []
_HASH_FUNCTION = None
_HASH_FORMAT = None

def _attempt_init_of_python_3_9_hash_object(hash_function_object, sys_used=sys):
    """Python 3.9 and onwards lets us initialize the hash function object with the
    key "usedforsecurity"=false. This lets us continue to use algorithms that have
    been deprecated either by FIPS or by Python itself, as the MD5 algorithm SCons
    prefers is not being used for security purposes as much as a short, 32 char
    hash that is resistant to accidental collisions.

    In prior versions of python, hashlib returns a native function wrapper, which
    errors out when it's queried for the optional parameter, so this function
    wraps that call.

    It can still throw a ValueError if the initialization fails due to FIPS
    compliance issues, but that is assumed to be the responsibility of the caller.
    """
    if hash_function_object is None:
        return None
    
    # https://stackoverflow.com/a/11887885 details how to check versions with the "packaging" library.
    # however, for our purposes checking the version is greater than or equal to 3.9 is good enough, as
    # the API is guaranteed to have support for the 'usedforsecurity' flag in 3.9. See 
    # https://docs.python.org/3/library/hashlib.html#:~:text=usedforsecurity for the version support notes.
    if (sys_used.version_info.major > 3) or (sys_used.version_info.major == 3 and sys_used.version_info.minor >= 9):
        return hash_function_object(usedforsecurity=False)

    # note that this can throw a ValueError in FIPS-enabled versions of Linux prior to 3.9
    # the OpenSSL hashlib will throw on first init here, but that is assumed to be responsibility of
    # the caller to diagnose the ValueError & potentially display the error to screen.
    return hash_function_object()

def _set_allowed_viable_default_hashes(hashlib_used, sys_used=sys):
    """Checks if SCons has ability to call the default algorithms normally supported.

    This util class is sometimes called prior to setting the user-selected hash algorithm,
    meaning that on FIPS-compliant systems the library would default-initialize MD5
    and throw an exception in set_hash_format. A common case is using the SConf options,
    which can run prior to main, and thus ignore the options.hash_format variable.

    This function checks the DEFAULT_HASH_FORMATS and sets the ALLOWED_HASH_FORMATS
    to only the ones that can be called. In Python >= 3.9 this will always default to
    MD5 as in Python 3.9 there is an optional attribute "usedforsecurity" set for the method.

    Throws if no allowed hash formats are detected.
    """
    global ALLOWED_HASH_FORMATS
    _last_error = None
    # note: if you call this method repeatedly, example using timeout, this is needed.
    # otherwise it keeps appending valid formats to the string
    ALLOWED_HASH_FORMATS = []
    
    for test_algorithm in DEFAULT_HASH_FORMATS:
        _test_hash = getattr(hashlib_used, test_algorithm, None)
        # we know hashlib claims to support it... check to see if we can call it.
        if _test_hash is not None:
            # the hashing library will throw an exception on initialization in FIPS mode,
            # meaning if we call the default algorithm returned with no parameters, it'll
            # throw if it's a bad algorithm, otherwise it will append it to the known
            # good formats.
            try:
                _attempt_init_of_python_3_9_hash_object(_test_hash, sys_used)
                ALLOWED_HASH_FORMATS.append(test_algorithm)
            except ValueError as e:
                _last_error = e
                continue
    
    if len(ALLOWED_HASH_FORMATS) == 0:
        from SCons.Errors import SConsEnvironmentError  # pylint: disable=import-outside-toplevel
        # chain the exception thrown with the most recent error from hashlib.
        raise SConsEnvironmentError(
            'No usable hash algorithms found.'
            'Most recent error from hashlib attached in trace.'
        ) from _last_error
    return

_set_allowed_viable_default_hashes(hashlib)


def get_hash_format():
    """Retrieves the hash format or ``None`` if not overridden.

    A return value of ``None``
    does not guarantee that MD5 is being used; instead, it means that the
    default precedence order documented in :func:`SCons.Util.set_hash_format`
    is respected.
    """
    return _HASH_FORMAT

def _attempt_get_hash_function(hash_name, hashlib_used=hashlib, sys_used=sys):
    """Wrapper used to try to initialize a hash function given.

    If successful, returns the name of the hash function back to the user.

    Otherwise returns None.
    """
    try:
        _fetch_hash = getattr(hashlib_used, hash_name, None)
        if _fetch_hash is None:
            return None
        _attempt_init_of_python_3_9_hash_object(_fetch_hash, sys_used)
        return hash_name
    except ValueError:
        # if attempt_init_of_python_3_9 throws, this is typically due to FIPS being enabled
        # however, if we get to this point, the viable hash function check has either been
        # bypassed or otherwise failed to properly restrict the user to only the supported
        # functions. As such throw the UserError as an internal assertion-like error.
        return None

def set_hash_format(hash_format, hashlib_used=hashlib, sys_used=sys):
    """Sets the default hash format used by SCons.

    If `hash_format` is ``None`` or
    an empty string, the default is determined by this function.

    Currently the default behavior is to use the first available format of
    the following options: MD5, SHA1, SHA256.
    """
    global _HASH_FORMAT, _HASH_FUNCTION

    _HASH_FORMAT = hash_format
    if hash_format:
        hash_format_lower = hash_format.lower()
        if hash_format_lower not in ALLOWED_HASH_FORMATS:
            from SCons.Errors import UserError  # pylint: disable=import-outside-toplevel

            # user can select something not supported by their OS but normally supported by
            # SCons, example, selecting MD5 in an OS with FIPS-mode turned on. Therefore we first
            # check if SCons supports it, and then if their local OS supports it.
            if hash_format_lower in DEFAULT_HASH_FORMATS:
                raise UserError('While hash format "%s" is supported by SCons, the '
                        'local system indicates only the following hash '
                        'formats are supported by the hashlib library: %s' %
                        (hash_format_lower,
                        ', '.join(ALLOWED_HASH_FORMATS))
                )
            else:
                # the hash format isn't supported by SCons in any case. Warn the user, and
                # if we detect that SCons supports more algorithms than their local system
                # supports, warn the user about that too.
                if ALLOWED_HASH_FORMATS == DEFAULT_HASH_FORMATS:
                    raise UserError('Hash format "%s" is not supported by SCons. Only '
                            'the following hash formats are supported: %s' %
                            (hash_format_lower,
                             ', '.join(ALLOWED_HASH_FORMATS))
                    )
                else:
                    raise UserError('Hash format "%s" is not supported by SCons. '
                            'SCons supports more hash formats than your local system '
                            'is reporting; SCons supports: %s. Your local system only '
                            'supports: %s' %
                            (hash_format_lower,
                             ', '.join(DEFAULT_HASH_FORMATS), 
                             ', '.join(ALLOWED_HASH_FORMATS))
                    )

        # this is not expected to fail. If this fails it means the set_allowed_viable_default_hashes
        # function did not throw, or when it threw, the exception was caught and ignored, or
        # the global ALLOWED_HASH_FORMATS was changed by an external user.
        _HASH_FUNCTION = _attempt_get_hash_function(hash_format_lower, hashlib_used, sys_used)
        
        if _HASH_FUNCTION is None:
            from SCons.Errors import UserError  # pylint: disable=import-outside-toplevel

            raise UserError(
                'Hash format "%s" is not available in your Python interpreter. '
                'Expected to be supported algorithm by set_allowed_viable_default_hashes, '
                'Assertion error in SCons.'
                % hash_format_lower
            )
    else:
        # Set the default hash format based on what is available, defaulting
        # to the first supported hash algorithm (usually md5) for backwards compatibility.
        # in FIPS-compliant systems this usually defaults to SHA1, unless that too has been
        # disabled.
        for choice in ALLOWED_HASH_FORMATS:
            _HASH_FUNCTION = _attempt_get_hash_function(choice, hashlib_used, sys_used)
            
            if _HASH_FUNCTION is not None:
                break
        else:
            # This is not expected to happen in practice.
            from SCons.Errors import UserError  # pylint: disable=import-outside-toplevel

            raise UserError(
                'Your Python interpreter does not have MD5, SHA1, or SHA256. '
                'SCons requires at least one. Expected to support one or more '
                'during set_allowed_viable_default_hashes.'
            )

# Ensure that this is initialized in case either:
#    1. This code is running in a unit test.
#    2. This code is running in a consumer that does hash operations while
#       SConscript files are being loaded.
set_hash_format(None)


def get_current_hash_algorithm_used():
    """Returns the current hash algorithm name used.
    
    Where the python version >= 3.9, this is expected to return md5.
    If python's version is <= 3.8, this returns md5 on non-FIPS-mode platforms, and
    sha1 or sha256 on FIPS-mode Linux platforms.

    This function is primarily useful for testing, where one expects a value to be
    one of N distinct hashes, and therefore the test needs to know which hash to select.
    """
    return _HASH_FUNCTION

def _get_hash_object(hash_format, hashlib_used=hashlib, sys_used=sys):
    """Allocates a hash object using the requested hash format.

    Args:
        hash_format: Hash format to use.

    Returns:
        hashlib object.
    """
    if hash_format is None:
        if _HASH_FUNCTION is None:
            from SCons.Errors import UserError  # pylint: disable=import-outside-toplevel

            raise UserError('There is no default hash function. Did you call '
                            'a hashing function before SCons was initialized?')
        return _attempt_init_of_python_3_9_hash_object(getattr(hashlib_used, _HASH_FUNCTION, None), sys_used)

    if not hasattr(hashlib, hash_format):
        from SCons.Errors import UserError  # pylint: disable=import-outside-toplevel

        raise UserError(
            'Hash format "%s" is not available in your Python interpreter.' %
            hash_format)

    return _attempt_init_of_python_3_9_hash_object(getattr(hashlib, hash_format), sys_used)


def hash_signature(s, hash_format=None):
    """
    Generate hash signature of a string

    Args:
        s: either string or bytes. Normally should be bytes
        hash_format: Specify to override default hash format

    Returns:
        String of hex digits representing the signature
    """
    m = _get_hash_object(hash_format)
    try:
        m.update(to_bytes(s))
    except TypeError:
        m.update(to_bytes(str(s)))

    return m.hexdigest()


def hash_file_signature(fname, chunksize=65536, hash_format=None):
    """
    Generate the md5 signature of a file

    Args:
        fname: file to hash
        chunksize: chunk size to read
        hash_format: Specify to override default hash format

    Returns:
        String of Hex digits representing the signature
    """

    m = _get_hash_object(hash_format)
    with open(fname, "rb") as f:
        while True:
            blck = f.read(chunksize)
            if not blck:
                break
            m.update(to_bytes(blck))
    return m.hexdigest()


def hash_collect(signatures, hash_format=None):
    """
    Collects a list of signatures into an aggregate signature.

    Args:
        signatures: a list of signatures
        hash_format: Specify to override default hash format

    Returns:
        the aggregate signature
    """

    if len(signatures) == 1:
        return signatures[0]

    return hash_signature(', '.join(signatures), hash_format)


_MD5_WARNING_SHOWN = False

def _show_md5_warning(function_name):
    """Shows a deprecation warning for various MD5 functions."""

    global _MD5_WARNING_SHOWN

    if not _MD5_WARNING_SHOWN:
        import SCons.Warnings  # pylint: disable=import-outside-toplevel

        SCons.Warnings.warn(SCons.Warnings.DeprecatedWarning,
                            "Function %s is deprecated" % function_name)
        _MD5_WARNING_SHOWN = True


def MD5signature(s):
    """Deprecated. Use :func:`hash_signature` instead."""

    _show_md5_warning("MD5signature")
    return hash_signature(s)


def MD5filesignature(fname, chunksize=65536):
    """Deprecated. Use :func:`hash_file_signature` instead."""

    _show_md5_warning("MD5filesignature")
    return hash_file_signature(fname, chunksize)


def MD5collect(signatures):
    """Deprecated. Use :func:`hash_collect` instead."""

    _show_md5_warning("MD5collect")
    return hash_collect(signatures)


def silent_intern(x):
    """
    Perform :mod:`sys.intern` on the passed argument and return the result.
    If the input is ineligible for interning the original argument is
    returned and no exception is thrown.
    """
    try:
        return sys.intern(x)
    except TypeError:
        return x


# From Dinu C. Gherman,
# Python Cookbook, second edition, recipe 6.17, p. 277.
# Also: https://code.activestate.com/recipes/68205
# ASPN: Python Cookbook: Null Object Design Pattern

class Null:
    """ Null objects always and reliably "do nothing." """
    def __new__(cls, *args, **kwargs):
        if '_instance' not in vars(cls):
            cls._instance = super(Null, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    def __init__(self, *args, **kwargs):
        pass
    def __call__(self, *args, **kwargs):
        return self
    def __repr__(self):
        return "Null(0x%08X)" % id(self)
    def __bool__(self):
        return False
    def __getattr__(self, name):
        return self
    def __setattr__(self, name, value):
        return self
    def __delattr__(self, name):
        return self


class NullSeq(Null):
    """ A Null object that can also be iterated over. """
    def __len__(self):
        return 0
    def __iter__(self):
        return iter(())
    def __getitem__(self, i):
        return self
    def __delitem__(self, i):
        return self
    def __setitem__(self, i, v):
        return self


def to_bytes(s) -> bytes:
    if s is None:
        return b'None'
    if isinstance(s, (bytes, bytearray)):
        # if already bytes return.
        return s
    return bytes(s, 'utf-8')


def to_str(s) -> str:
    if s is None:
        return 'None'
    if is_String(s):
        return s
    return str(s, 'utf-8')


def cmp(a, b) -> bool:
    """A cmp function because one is no longer available in python3."""
    return (a > b) - (a < b)


def get_env_bool(env, name, default=False) -> bool:
    """Convert a construction variable to bool.

    If the value of `name` in `env` is 'true', 'yes', 'y', 'on' (case
    insensitive) or anything convertible to int that yields non-zero then
    return ``True``; if 'false', 'no', 'n', 'off' (case insensitive)
    or a number that converts to integer zero return ``False``.
    Otherwise, return `default`.

    Args:
        env: construction environment, or any dict-like object
        name: name of the variable
        default: value to return if `name` not in `env` or cannot
          be converted (default: False)

    Returns:
        the "truthiness" of `name`
    """
    try:
        var = env[name]
    except KeyError:
        return default
    try:
        return bool(int(var))
    except ValueError:
        if str(var).lower() in ('true', 'yes', 'y', 'on'):
            return True

        if str(var).lower() in ('false', 'no', 'n', 'off'):
            return False

        return default


def get_os_env_bool(name, default=False) -> bool:
    """Convert an environment variable to bool.

    Conversion is the same as for :func:`get_env_bool`.
    """
    return get_env_bool(os.environ, name, default)


def print_time():
    """Hack to return a value from Main if can't import Main."""
    # pylint: disable=redefined-outer-name,import-outside-toplevel
    from SCons.Script.Main import print_time
    return print_time

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
