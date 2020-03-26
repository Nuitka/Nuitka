"""SCons.Util

Various utility functions go here.
"""
#
# Copyright (c) 2001 - 2019 The SCons Foundation
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

__revision__ = "src/engine/SCons/Util.py bee7caf9defd6e108fc2998a2520ddb36a967691 2019-12-17 02:07:09 bdeegan"

import os
import sys
import copy
import re
import types
import codecs
import pprint
import hashlib

PY3 = sys.version_info[0] == 3

try:
    from collections import UserDict, UserList, UserString
except ImportError:
    from UserDict import UserDict
    from UserList import UserList
    from UserString import UserString

try:
    from collections.abc import Iterable, MappingView
except ImportError:
    from collections import Iterable

from collections import OrderedDict

# Don't "from types import ..." these because we need to get at the
# types module later to look for UnicodeType.

# Below not used?
# InstanceType    = types.InstanceType

MethodType      = types.MethodType
FunctionType    = types.FunctionType

try:
    _ = type(unicode)
except NameError:
    UnicodeType = str
else:
    UnicodeType = unicode

def dictify(keys, values, result={}):
    for k, v in zip(keys, values):
        result[k] = v
    return result

_altsep = os.altsep
if _altsep is None and sys.platform == 'win32':
    # My ActivePython 2.0.1 doesn't set os.altsep!  What gives?
    _altsep = '/'
if _altsep:
    def rightmost_separator(path, sep):
        return max(path.rfind(sep), path.rfind(_altsep))
else:
    def rightmost_separator(path, sep):
        return path.rfind(sep)

# First two from the Python Cookbook, just for completeness.
# (Yeah, yeah, YAGNI...)
def containsAny(str, set):
    """Check whether sequence str contains ANY of the items in set."""
    for c in set:
        if c in str: return 1
    return 0

def containsAll(str, set):
    """Check whether sequence str contains ALL of the items in set."""
    for c in set:
        if c not in str: return 0
    return 1

def containsOnly(str, set):
    """Check whether sequence str contains ONLY items in set."""
    for c in str:
        if c not in set: return 0
    return 1

def splitext(path):
    """Same as os.path.splitext() but faster."""
    sep = rightmost_separator(path, os.sep)
    dot = path.rfind('.')
    # An ext is only real if it has at least one non-digit char
    if dot > sep and not containsOnly(path[dot:], "0123456789."):
        return path[:dot],path[dot:]
    else:
        return path,""

def updrive(path):
    """
    Make the drive letter (if any) upper case.
    This is useful because Windows is inconsistent on the case
    of the drive letter, which can cause inconsistencies when
    calculating command signatures.
    """
    drive, rest = os.path.splitdrive(path)
    if drive:
        path = drive.upper() + rest
    return path

class NodeList(UserList):
    """This class is almost exactly like a regular list of Nodes
    (actually it can hold any object), with one important difference.
    If you try to get an attribute from this list, it will return that
    attribute from every item in the list.  For example:

    >>> someList = NodeList([ '  foo  ', '  bar  ' ])
    >>> someList.strip()
    [ 'foo', 'bar' ]
    """

#     def __init__(self, initlist=None):
#         self.data = []
# #        print("TYPE:%s"%type(initlist))
#         if initlist is not None:
#             # XXX should this accept an arbitrary sequence?
#             if type(initlist) == type(self.data):
#                 self.data[:] = initlist
#             elif isinstance(initlist, (UserList, NodeList)):
#                 self.data[:] = initlist.data[:]
#             elif isinstance(initlist, Iterable):
#                 self.data = list(initlist)
#             else:
#                 self.data = [ initlist,]


    def __nonzero__(self):
        return len(self.data) != 0

    def __bool__(self):
        return self.__nonzero__()

    def __str__(self):
        return ' '.join(map(str, self.data))

    def __iter__(self):
        return iter(self.data)

    def __call__(self, *args, **kwargs):
        result = [x(*args, **kwargs) for x in self.data]
        return self.__class__(result)

    def __getattr__(self, name):
        result = [getattr(x, name) for x in self.data]
        return self.__class__(result)

    def __getitem__(self, index):
        """
        This comes for free on py2,
        but py3 slices of NodeList are returning a list
        breaking slicing nodelist and refering to
        properties and methods on contained object
        """
#        return self.__class__(self.data[index])

        if isinstance(index, slice):
            # Expand the slice object using range()
            # limited by number of items in self.data
            indices = index.indices(len(self.data))
            return self.__class__([self[x] for x in
                    range(*indices)])
        else:
            # Return one item of the tart
            return self.data[index]


_get_env_var = re.compile(r'^\$([_a-zA-Z]\w*|{[_a-zA-Z]\w*})$')

def get_environment_var(varstr):
    """Given a string, first determine if it looks like a reference
    to a single environment variable, like "$FOO" or "${FOO}".
    If so, return that variable with no decorations ("FOO").
    If not, return None."""
    mo=_get_env_var.match(to_String(varstr))
    if mo:
        var = mo.group(1)
        if var[0] == '{':
            return var[1:-1]
        else:
            return var
    else:
        return None

class DisplayEngine(object):
    print_it = True
    def __call__(self, text, append_newline=1):
        if not self.print_it:
            return
        if append_newline: text = text + '\n'
        try:
            sys.stdout.write(UnicodeType(text))
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


def render_tree(root, child_func, prune=0, margin=[0], visited=None):
    """
    Render a tree of nodes into an ASCII tree view.

    :Parameters:
        - `root`:       the root node of the tree
        - `child_func`: the function called to get the children of a node
        - `prune`:      don't visit the same node twice
        - `margin`:     the format of the left margin to use for children of root. 1 results in a pipe, and 0 results in no pipe.
        - `visited`:    a dictionary of visited nodes in the current branch if not prune, or in the whole tree if prune.
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
    visited[rname] = 1

    for i in range(len(children)):
        margin.append(i < len(children)-1)
        retval = retval + render_tree(children[i], child_func, prune, margin, visited)
        margin.pop()

    return retval

IDX = lambda N: N and 1 or 0


def print_tree(root, child_func, prune=0, showtags=0, margin=[0], visited=None):
    """
    Print a tree of nodes.  This is like render_tree, except it prints
    lines directly instead of creating a string representation in memory,
    so that huge trees can be printed.

    :Parameters:
        - `root`       - the root node of the tree
        - `child_func` - the function called to get the children of a node
        - `prune`      - don't visit the same node twice
        - `showtags`   - print status information to the left of each node line
        - `margin`     - the format of the left margin to use for children of root. 1 results in a pipe, and 0 results in no pipe.
        - `visited`    - a dictionary of visited nodes in the current branch if not prune, or in the whole tree if prune.
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

        tags = ['[']
        tags.append(' E'[IDX(root.exists())])
        tags.append(' R'[IDX(root.rexists() and not root.exists())])
        tags.append(' BbB'[[0,1][IDX(root.has_explicit_builder())] +
                           [0,2][IDX(root.has_builder())]])
        tags.append(' S'[IDX(root.side_effect)])
        tags.append(' P'[IDX(root.precious)])
        tags.append(' A'[IDX(root.always_build)])
        tags.append(' C'[IDX(root.is_up_to_date())])
        tags.append(' N'[IDX(root.noclean)])
        tags.append(' H'[IDX(root.nocache)])
        tags.append(']')

    else:
        tags = []

    def MMM(m):
        return ["  ","| "][m]
    margins = list(map(MMM, margin[:-1]))

    children = child_func(root)

    if prune and rname in visited and children:
        sys.stdout.write(''.join(tags + margins + ['+-[', rname, ']']) + '\n')
        return

    sys.stdout.write(''.join(tags + margins + ['+-', rname]) + '\n')

    visited[rname] = 1

    if children:
        margin.append(1)
        idx = IDX(showtags)
        for C in children[:-1]:
            print_tree(C, child_func, prune, idx, margin, visited)
        margin[-1] = 0
        print_tree(children[-1], child_func, prune, idx, margin, visited)
        margin.pop()



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

DictTypes = (dict, UserDict)
ListTypes = (list, UserList)

try:
    # Handle getting dictionary views.
    SequenceTypes = (list, tuple, UserList, MappingView)
except NameError:
    SequenceTypes = (list, tuple, UserList)


# Note that profiling data shows a speed-up when comparing
# explicitly with str and unicode instead of simply comparing
# with basestring. (at least on Python 2.5.1)
try:
    StringTypes = (str, unicode, UserString)
except NameError:
    StringTypes = (str, UserString)

# Empirically, it is faster to check explicitly for str and
# unicode than for basestring.
try:
    BaseStringTypes = (str, unicode)
except NameError:
    BaseStringTypes = (str)

def is_Dict(obj, isinstance=isinstance, DictTypes=DictTypes):
    return isinstance(obj, DictTypes)

def is_List(obj, isinstance=isinstance, ListTypes=ListTypes):
    return isinstance(obj, ListTypes)

def is_Sequence(obj, isinstance=isinstance, SequenceTypes=SequenceTypes):
    return isinstance(obj, SequenceTypes)

def is_Tuple(obj, isinstance=isinstance, tuple=tuple):
    return isinstance(obj, tuple)

def is_String(obj, isinstance=isinstance, StringTypes=StringTypes):
    return isinstance(obj, StringTypes)

def is_Scalar(obj, isinstance=isinstance, StringTypes=StringTypes, SequenceTypes=SequenceTypes):
    # Profiling shows that there is an impressive speed-up of 2x
    # when explicitly checking for strings instead of just not
    # sequence when the argument (i.e. obj) is already a string.
    # But, if obj is a not string then it is twice as fast to
    # check only for 'not sequence'. The following code therefore
    # assumes that the obj argument is a string most of the time.
    return isinstance(obj, StringTypes) or not isinstance(obj, SequenceTypes)

def do_flatten(sequence, result, isinstance=isinstance,
               StringTypes=StringTypes, SequenceTypes=SequenceTypes):
    for item in sequence:
        if isinstance(item, StringTypes) or not isinstance(item, SequenceTypes):
            result.append(item)
        else:
            do_flatten(item, result)

def flatten(obj, isinstance=isinstance, StringTypes=StringTypes,
            SequenceTypes=SequenceTypes, do_flatten=do_flatten):
    """Flatten a sequence to a non-nested list.

    Flatten() converts either a single scalar or a nested sequence
    to a non-nested list. Note that flatten() considers strings
    to be scalars instead of sequences like Python would.
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

def flatten_sequence(sequence, isinstance=isinstance, StringTypes=StringTypes,
                     SequenceTypes=SequenceTypes, do_flatten=do_flatten):
    """Flatten a sequence to a non-nested list.

    Same as flatten(), but it does not handle the single scalar
    case. This is slightly more efficient when one knows that
    the sequence to flatten can not be a scalar.
    """
    result = []
    for item in sequence:
        if isinstance(item, StringTypes) or not isinstance(item, SequenceTypes):
            result.append(item)
        else:
            do_flatten(item, result)
    return result

# Generic convert-to-string functions that abstract away whether or
# not the Python we're executing has Unicode support.  The wrapper
# to_String_for_signature() will use a for_signature() method if the
# specified object has one.
#
def to_String(s,
              isinstance=isinstance, str=str,
              UserString=UserString, BaseStringTypes=BaseStringTypes):
    if isinstance(s,BaseStringTypes):
        # Early out when already a string!
        return s
    elif isinstance(s, UserString):
        # s.data can only be either a unicode or a regular
        # string. Please see the UserString initializer.
        return s.data
    else:
        return str(s)

def to_String_for_subst(s,
                        isinstance=isinstance, str=str, to_String=to_String,
                        BaseStringTypes=BaseStringTypes, SequenceTypes=SequenceTypes,
                        UserString=UserString):

    # Note that the test cases are sorted by order of probability.
    if isinstance(s, BaseStringTypes):
        return s
    elif isinstance(s, SequenceTypes):
        return ' '.join([to_String_for_subst(e) for e in s])
    elif isinstance(s, UserString):
        # s.data can only be either a unicode or a regular
        # string. Please see the UserString initializer.
        return s.data
    else:
        return str(s)

def to_String_for_signature(obj, to_String_for_subst=to_String_for_subst,
                            AttributeError=AttributeError):
    try:
        f = obj.for_signature
    except AttributeError:
        if isinstance(obj, dict):
            # pprint will output dictionary in key sorted order
            # with py3.5 the order was randomized. In general depending on dictionary order
            # which was undefined until py3.6 (where it's by insertion order) was not wise.
            return pprint.pformat(obj, width=1000000)
        else:
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

_semi_deepcopy_dispatch = d = {}

def semi_deepcopy_dict(x, exclude = [] ):
    copy = {}
    for key, val in x.items():
        # The regular Python copy.deepcopy() also deepcopies the key,
        # as follows:
        #
        #    copy[semi_deepcopy(key)] = semi_deepcopy(val)
        #
        # Doesn't seem like we need to, but we'll comment it just in case.
        if key not in exclude:
            copy[key] = semi_deepcopy(val)
    return copy
d[dict] = semi_deepcopy_dict

def _semi_deepcopy_list(x):
    return list(map(semi_deepcopy, x))
d[list] = _semi_deepcopy_list

def _semi_deepcopy_tuple(x):
    return tuple(map(semi_deepcopy, x))
d[tuple] = _semi_deepcopy_tuple

def semi_deepcopy(x):
    copier = _semi_deepcopy_dispatch.get(type(x))
    if copier:
        return copier(x)
    else:
        if hasattr(x, '__semi_deepcopy__') and callable(x.__semi_deepcopy__):
            return x.__semi_deepcopy__()
        elif isinstance(x, UserDict):
            return x.__class__(semi_deepcopy_dict(x))
        elif isinstance(x, UserList):
            return x.__class__(_semi_deepcopy_list(x))

        return x


class Proxy(object):
    """A simple generic Proxy class, forwarding all calls to
    subject.  So, for the benefit of the python newbie, what does
    this really mean?  Well, it means that you can take an object, let's
    call it 'objA', and wrap it in this Proxy class, with a statement
    like this

                 proxyObj = Proxy(objA),

    Then, if in the future, you do something like this

                 x = proxyObj.var1,

    since Proxy does not have a 'var1' attribute (but presumably objA does),
    the request actually is equivalent to saying

                 x = objA.var1

    Inherit from this class to create a Proxy.

    Note that, with new-style classes, this does *not* work transparently
    for Proxy subclasses that use special .__*__() method names, because
    those names are now bound to the class, not the individual instances.
    You now need to know in advance which .__*__() method names you want
    to pass on to the underlying Proxy object, and specifically delegate
    their calls like this:

        class Foo(Proxy):
            __str__ = Delegate('__str__')
    """

    def __init__(self, subject):
        """Wrap an object as a Proxy object"""
        self._subject = subject

    def __getattr__(self, name):
        """Retrieve an attribute from the wrapped object.  If the named
           attribute doesn't exist, AttributeError is raised"""
        return getattr(self._subject, name)

    def get(self):
        """Retrieve the entire wrapped object"""
        return self._subject

    def __eq__(self, other):
        if issubclass(other.__class__, self._subject.__class__):
            return self._subject == other
        return self.__dict__ == other.__dict__

class Delegate(object):
    """A Python Descriptor class that delegates attribute fetches
    to an underlying wrapped subject of a Proxy.  Typical use:

        class Foo(Proxy):
            __str__ = Delegate('__str__')
    """
    def __init__(self, attribute):
        self.attribute = attribute
    def __get__(self, obj, cls):
        if isinstance(obj, cls):
            return getattr(obj._subject, self.attribute)
        else:
            return self

# attempt to load the windows registry module:
can_read_reg = 0
try:
    import winreg

    can_read_reg = 1
    hkey_mod = winreg

    RegOpenKeyEx    = winreg.OpenKeyEx
    RegEnumKey      = winreg.EnumKey
    RegEnumValue    = winreg.EnumValue
    RegQueryValueEx = winreg.QueryValueEx
    RegError        = winreg.error

except ImportError:
    try:
        import win32api
        import win32con
        can_read_reg = 1
        hkey_mod = win32con

        RegOpenKeyEx    = win32api.RegOpenKeyEx
        RegEnumKey      = win32api.RegEnumKey
        RegEnumValue    = win32api.RegEnumValue
        RegQueryValueEx = win32api.RegQueryValueEx
        RegError        = win32api.error

    except ImportError:
        class _NoError(Exception):
            pass
        RegError = _NoError


# Make sure we have a definition of WindowsError so we can
# run platform-independent tests of Windows functionality on
# platforms other than Windows.  (WindowsError is, in fact, an
# OSError subclass on Windows.)

class PlainWindowsError(OSError):
    pass

try:
    WinError = WindowsError
except NameError:
    WinError = PlainWindowsError


if can_read_reg:
    HKEY_CLASSES_ROOT  = hkey_mod.HKEY_CLASSES_ROOT
    HKEY_LOCAL_MACHINE = hkey_mod.HKEY_LOCAL_MACHINE
    HKEY_CURRENT_USER  = hkey_mod.HKEY_CURRENT_USER
    HKEY_USERS         = hkey_mod.HKEY_USERS

    def RegGetValue(root, key):
        r"""This utility function returns a value in the registry
        without having to open the key first.  Only available on
        Windows platforms with a version of Python that can read the
        registry.  Returns the same thing as
        SCons.Util.RegQueryValueEx, except you just specify the entire
        path to the value, and don't have to bother opening the key
        first.  So:

        Instead of:
          k = SCons.Util.RegOpenKeyEx(SCons.Util.HKEY_LOCAL_MACHINE,
                r'SOFTWARE\Microsoft\Windows\CurrentVersion')
          out = SCons.Util.RegQueryValueEx(k,
                'ProgramFilesDir')

        You can write:
          out = SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE,
                r'SOFTWARE\Microsoft\Windows\CurrentVersion\ProgramFilesDir')
        """
        # I would use os.path.split here, but it's not a filesystem
        # path...
        p = key.rfind('\\') + 1
        keyp = key[:p-1]          # -1 to omit trailing slash
        val = key[p:]
        k = RegOpenKeyEx(root, keyp)
        return RegQueryValueEx(k,val)
else:
    HKEY_CLASSES_ROOT = None
    HKEY_LOCAL_MACHINE = None
    HKEY_CURRENT_USER = None
    HKEY_USERS = None

    def RegGetValue(root, key):
        raise WinError

    def RegOpenKeyEx(root, key):
        raise WinError

if sys.platform == 'win32':

    def WhereIs(file, path=None, pathext=None, reject=[]):
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
        if not is_List(reject) and not is_Tuple(reject):
            reject = [reject]
        for dir in path:
            f = os.path.join(dir, file)
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

    def WhereIs(file, path=None, pathext=None, reject=[]):
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
        if not is_List(reject) and not is_Tuple(reject):
            reject = [reject]
        for dir in path:
            f = os.path.join(dir, file)
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

    def WhereIs(file, path=None, pathext=None, reject=[]):
        import stat
        if path is None:
            try:
                path = os.environ['PATH']
            except KeyError:
                return None
        if is_String(path):
            path = path.split(os.pathsep)
        if not is_List(reject) and not is_Tuple(reject):
            reject = [reject]
        for d in path:
            f = os.path.join(d, file)
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

def PrependPath(oldpath, newpath, sep = os.pathsep,
                delete_existing=1, canonicalize=None):
    """This prepends newpath elements to the given oldpath.  Will only
    add any particular path once (leaving the first one it encounters
    and ignoring the rest, to preserve path order), and will
    os.path.normpath and os.path.normcase all paths to help assure
    this.  This can also handle the case where the given old path
    variable is a list instead of a string, in which case a list will
    be returned instead of a string.

    Example:
      Old Path: "/foo/bar:/foo"
      New Path: "/biz/boom:/foo"
      Result:   "/biz/boom:/foo:/foo/bar"

    If delete_existing is 0, then adding a path that exists will
    not move it to the beginning; it will stay where it is in the
    list.

    If canonicalize is not None, it is applied to each element of
    newpath before use.
    """

    orig = oldpath
    is_list = 1
    paths = orig
    if not is_List(orig) and not is_Tuple(orig):
        paths = paths.split(sep)
        is_list = 0

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
    else:
        return sep.join(paths)

def AppendPath(oldpath, newpath, sep = os.pathsep,
               delete_existing=1, canonicalize=None):
    """This appends new path elements to the given old path.  Will
    only add any particular path once (leaving the last one it
    encounters and ignoring the rest, to preserve path order), and
    will os.path.normpath and os.path.normcase all paths to help
    assure this.  This can also handle the case where the given old
    path variable is a list instead of a string, in which case a list
    will be returned instead of a string.

    Example:
      Old Path: "/foo/bar:/foo"
      New Path: "/biz/boom:/foo"
      Result:   "/foo/bar:/biz/boom:/foo"

    If delete_existing is 0, then adding a path that exists
    will not move it to the end; it will stay where it is in the list.

    If canonicalize is not None, it is applied to each element of
    newpath before use.
    """

    orig = oldpath
    is_list = 1
    paths = orig
    if not is_List(orig) and not is_Tuple(orig):
        paths = paths.split(sep)
        is_list = 0

    if is_String(newpath):
        newpaths = newpath.split(sep)
    elif not is_List(newpath) and not is_Tuple(newpath):
        newpaths = [ newpath ]  # might be a Dir
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
    else:
        return sep.join(paths)

def AddPathIfNotExists(env_dict, key, path, sep=os.pathsep):
    """This function will take 'key' out of the dictionary
    'env_dict', then add the path 'path' to that key if it is not
    already there.  This treats the value of env_dict[key] as if it
    has a similar format to the PATH variable...a list of paths
    separated by tokens.  The 'path' will get added to the list if it
    is not already there."""
    try:
        is_list = 1
        paths = env_dict[key]
        if not is_List(env_dict[key]):
            paths = paths.split(sep)
            is_list = 0
        if os.path.normcase(path) not in list(map(os.path.normcase, paths)):
            paths = [ path ] + paths
        if is_list:
            env_dict[key] = paths
        else:
            env_dict[key] = sep.join(paths)
    except KeyError:
        env_dict[key] = path

if sys.platform == 'cygwin':
    def get_native_path(path):
        """Transforms an absolute path into a native path for the system.  In
        Cygwin, this converts from a Cygwin path to a Windows one."""
        with os.popen('cygpath -w ' + path) as p:
            npath = p.read().replace('\n', '')
        return npath
else:
    def get_native_path(path):
        """Transforms an absolute path into a native path for the system.
        Non-Cygwin version, just leave the path alone."""
        return path

display = DisplayEngine()

def Split(arg):
    if is_List(arg) or is_Tuple(arg):
        return arg
    elif is_String(arg):
        return arg.split()
    else:
        return [arg]

class CLVar(UserList):
    """A class for command-line construction variables.

    This is a list that uses Split() to split an initial string along
    white-space arguments, and similarly to split any strings that get
    added.  This allows us to Do the Right Thing with Append() and
    Prepend() (as well as straight Python foo = env['VAR'] + 'arg1
    arg2') regardless of whether a user adds a list or a string to a
    command-line construction variable.
    """
    def __init__(self, seq = []):
        UserList.__init__(self, Split(seq))
    def __add__(self, other):
        return UserList.__add__(self, CLVar(other))
    def __radd__(self, other):
        return UserList.__radd__(self, CLVar(other))
    def __str__(self):
        return ' '.join(self.data)


class Selector(OrderedDict):
    """A callable ordered dictionary that maps file suffixes to
    dictionary values.  We preserve the order in which items are added
    so that get_suffix() calls always return the first suffix added."""
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
    def case_sensitive_suffixes(s1, s2):
        return 0
else:
    def case_sensitive_suffixes(s1, s2):
        return (os.path.normcase(s1) != os.path.normcase(s2))

def adjustixes(fname, pre, suf, ensure_suffix=False):
    if pre:
        path, fn = os.path.split(os.path.normpath(fname))
        if fn[:len(pre)] != pre:
            fname = os.path.join(path, pre + fn)
    # Only append a suffix if the suffix we're going to add isn't already
    # there, and if either we've been asked to ensure the specific suffix
    # is present or there's no suffix on it at all.
    if suf and fname[-len(suf):] != suf and \
       (ensure_suffix or not splitext(fname)[1]):
            fname = fname + suf
    return fname



# From Tim Peters,
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52560
# ASPN: Python Cookbook: Remove duplicates from a sequence
# (Also in the printed Python Cookbook.)

def unique(s):
    """Return a list of the elements in s, but without duplicates.

    For example, unique([1,2,3,1,2,3]) is some permutation of [1,2,3],
    unique("abcabc") some permutation of ["a", "b", "c"], and
    unique(([1, 2], [2, 3], [1, 2])) some permutation of
    [[2, 3], [1, 2]].

    For best speed, all sequence elements should be hashable.  Then
    unique() will usually work in linear time.

    If not possible, the sequence elements should enjoy a total
    ordering, and if list(s).sort() doesn't raise TypeError it's
    assumed that they do enjoy a total ordering.  Then unique() will
    usually work in O(N*log2(N)) time.

    If that's not possible either, the sequence elements must support
    equality-testing.  Then unique() will usually work in quadratic
    time.
    """

    n = len(s)
    if n == 0:
        return []

    # Try using a dict first, as that's the fastest and will usually
    # work.  If it doesn't work, it will usually fail quickly, so it
    # usually doesn't cost much to *try* it.  It requires that all the
    # sequence elements be hashable, and support equality comparison.
    u = {}
    try:
        for x in s:
            u[x] = 1
    except TypeError:
        pass    # move on to the next method
    else:
        return list(u.keys())
    del u

    # We can't hash all the elements.  Second fastest is to sort,
    # which brings the equal elements together; then duplicates are
    # easy to weed out in a single pass.
    # NOTE:  Python's list.sort() was designed to be efficient in the
    # presence of many duplicate elements.  This isn't true of all
    # sort functions in all languages or libraries, so this approach
    # is more effective in Python than it may be elsewhere.
    try:
        t = sorted(s)
    except TypeError:
        pass    # move on to the next method
    else:
        assert n > 0
        last = t[0]
        lasti = i = 1
        while i < n:
            if t[i] != last:
                t[lasti] = last = t[i]
                lasti = lasti + 1
            i = i + 1
        return t[:lasti]
    del t

    # Brute force is all that's left.
    u = []
    for x in s:
        if x not in u:
            u.append(x)
    return u



# From Alex Martelli,
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52560
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
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result

# A more efficient implementation of Alex's uniquer(), this avoids the
# idfun() argument and function-call overhead by assuming that all
# items in the sequence are hashable.

def uniquer_hashables(seq):
    seen = {}
    result = []
    for item in seq:
        #if not item in seen:
        if item not in seen:
            seen[item] = 1
            result.append(item)
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


class LogicalLines(object):
    """ Wrapper class for the logical_lines method.

        Allows us to read all "logical" lines at once from a
        given file object.
    """

    def __init__(self, fileobj):
        self.fileobj = fileobj

    def readlines(self):
        result = [l for l in logical_lines(self.fileobj)]
        return result


class UniqueList(UserList):
    def __init__(self, seq = []):
        UserList.__init__(self, seq)
        self.unique = True
    def __make_unique(self):
        if not self.unique:
            self.data = uniquer_hashables(self.data)
            self.unique = True
    def __lt__(self, other):
        self.__make_unique()
        return UserList.__lt__(self, other)
    def __le__(self, other):
        self.__make_unique()
        return UserList.__le__(self, other)
    def __eq__(self, other):
        self.__make_unique()
        return UserList.__eq__(self, other)
    def __ne__(self, other):
        self.__make_unique()
        return UserList.__ne__(self, other)
    def __gt__(self, other):
        self.__make_unique()
        return UserList.__gt__(self, other)
    def __ge__(self, other):
        self.__make_unique()
        return UserList.__ge__(self, other)
    def __cmp__(self, other):
        self.__make_unique()
        return UserList.__cmp__(self, other)
    def __len__(self):
        self.__make_unique()
        return UserList.__len__(self)
    def __getitem__(self, i):
        self.__make_unique()
        return UserList.__getitem__(self, i)
    def __setitem__(self, i, item):
        UserList.__setitem__(self, i, item)
        self.unique = False
    def __getslice__(self, i, j):
        self.__make_unique()
        return UserList.__getslice__(self, i, j)
    def __setslice__(self, i, j, other):
        UserList.__setslice__(self, i, j, other)
        self.unique = False
    def __add__(self, other):
        result = UserList.__add__(self, other)
        result.unique = False
        return result
    def __radd__(self, other):
        result = UserList.__radd__(self, other)
        result.unique = False
        return result
    def __iadd__(self, other):
        result = UserList.__iadd__(self, other)
        result.unique = False
        return result
    def __mul__(self, other):
        result = UserList.__mul__(self, other)
        result.unique = False
        return result
    def __rmul__(self, other):
        result = UserList.__rmul__(self, other)
        result.unique = False
        return result
    def __imul__(self, other):
        result = UserList.__imul__(self, other)
        result.unique = False
        return result
    def append(self, item):
        UserList.append(self, item)
        self.unique = False
    def insert(self, i):
        UserList.insert(self, i)
        self.unique = False
    def count(self, item):
        self.__make_unique()
        return UserList.count(self, item)
    def index(self, item):
        self.__make_unique()
        return UserList.index(self, item)
    def reverse(self):
        self.__make_unique()
        UserList.reverse(self)
    def sort(self, *args, **kwds):
        self.__make_unique()
        return UserList.sort(self, *args, **kwds)
    def extend(self, other):
        UserList.extend(self, other)
        self.unique = False


class Unbuffered(object):
    """
    A proxy class that wraps a file object, flushing after every write,
    and delegating everything else to the wrapped object.
    """
    def __init__(self, file):
        self.file = file
        self.softspace = 0  ## backward compatibility; not supported in Py3k
    def write(self, arg):
        try:
            self.file.write(arg)
            self.file.flush()
        except IOError:
            # Stdout might be connected to a pipe that has been closed
            # by now. The most likely reason for the pipe being closed
            # is that the user has press ctrl-c. It this is the case,
            # then SCons is currently shutdown. We therefore ignore
            # IOError's here so that SCons can continue and shutdown
            # properly so that the .sconsign is correctly written
            # before SCons exits.
            pass
    def __getattr__(self, attr):
        return getattr(self.file, attr)

def make_path_relative(path):
    """ makes an absolute path name to a relative pathname.
    """
    if os.path.isabs(path):
        drive_s,path = os.path.splitdrive(path)

        import re
        if not drive_s:
            path=re.compile("/*(.*)").findall(path)[0]
        else:
            path=path[1:]

    assert( not os.path.isabs( path ) ), path
    return path



# The original idea for AddMethod() and RenameFunction() come from the
# following post to the ActiveState Python Cookbook:
#
#   ASPN: Python Cookbook : Install bound methods in an instance
#   http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/223613
#
# That code was a little fragile, though, so the following changes
# have been wrung on it:
#
# * Switched the installmethod() "object" and "function" arguments,
#   so the order reflects that the left-hand side is the thing being
#   "assigned to" and the right-hand side is the value being assigned.
#
# * Changed explicit type-checking to the "try: klass = object.__class__"
#   block in installmethod() below so that it still works with the
#   old-style classes that SCons uses.
#
# * Replaced the by-hand creation of methods and functions with use of
#   the "new" module, as alluded to in Alex Martelli's response to the
#   following Cookbook post:
#
#   ASPN: Python Cookbook : Dynamically added methods to a class
#   http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/81732

def AddMethod(obj, function, name=None):
    """
    Adds either a bound method to an instance or the function itself (or an unbound method in Python 2) to a class.
    If name is ommited the name of the specified function
    is used by default.

    Example::

        a = A()
        def f(self, x, y):
        self.z = x + y
        AddMethod(f, A, "add")
        a.add(2, 4)
        print(a.z)
        AddMethod(lambda self, i: self.l[i], a, "listIndex")
        print(a.listIndex(5))
    """
    if name is None:
        name = function.__name__
    else:
        function = RenameFunction(function, name)

    # Note the Python version checks - WLB
    # Python 3.3 dropped the 3rd parameter from types.MethodType
    if hasattr(obj, '__class__') and obj.__class__ is not type:
        # "obj" is an instance, so it gets a bound method.
        if sys.version_info[:2] > (3, 2):
            method = MethodType(function, obj)
        else:
            method = MethodType(function, obj, obj.__class__)
    else:
        # Handle classes
        method = function

    setattr(obj, name, method)

def RenameFunction(function, name):
    """
    Returns a function identical to the specified function, but with
    the specified name.
    """
    return FunctionType(function.__code__,
                        function.__globals__,
                        name,
                        function.__defaults__)


if hasattr(hashlib, 'md5'):
    md5 = True

    def MD5signature(s):
        """
        Generate md5 signature of a string

        :param s: either string or bytes. Normally should be bytes
        :return: String of hex digits representing the signature
        """
        m = hashlib.md5()

        try:
            m.update(to_bytes(s))
        except TypeError as e:
            m.update(to_bytes(str(s)))

        return m.hexdigest()

    def MD5filesignature(fname, chunksize=65536):
        """
        Generate the md5 signature of a file

        :param fname: file to hash
        :param chunksize: chunk size to read
        :return: String of Hex digits representing the signature
        """
        m = hashlib.md5()
        with open(fname, "rb") as f:
            while True:
                blck = f.read(chunksize)
                if not blck:
                    break
                m.update(to_bytes(blck))
        return m.hexdigest()
else:
    # if md5 algorithm not available, just return data unmodified
    # could add alternative signature scheme here
    md5 = False

    def MD5signature(s):
        return str(s)

    def MD5filesignature(fname, chunksize=65536):
        with open(fname, "rb") as f:
            result = f.read()
        return result


def MD5collect(signatures):
    """
    Collects a list of signatures into an aggregate signature.

    signatures - a list of signatures
    returns - the aggregate signature
    """
    if len(signatures) == 1:
        return signatures[0]
    else:
        return MD5signature(', '.join(signatures))


def silent_intern(x):
    """
    Perform sys.intern() on the passed argument and return the result.
    If the input is ineligible (e.g. a unicode string) the original argument is
    returned and no exception is thrown.
    """
    try:
        return sys.intern(x)
    except TypeError:
        return x



# From Dinu C. Gherman,
# Python Cookbook, second edition, recipe 6.17, p. 277.
# Also:
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/68205
# ASPN: Python Cookbook: Null Object Design Pattern

#TODO??? class Null(object):
class Null(object):
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
    def __nonzero__(self):
        return False
    def __bool__(self):
        return False
    def __getattr__(self, name):
        return self
    def __setattr__(self, name, value):
        return self
    def __delattr__(self, name):
        return self

class NullSeq(Null):
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


del __revision__


def to_bytes(s):
    if s is None:
        return b'None'
    if not PY3 and isinstance(s, UnicodeType):
        # PY2, must encode unicode
        return bytearray(s, 'utf-8')
    if isinstance (s, (bytes, bytearray)) or bytes is str:
        # Above case not covered here as py2 bytes and strings are the same
        return s
    return bytes(s, 'utf-8')


def to_str(s):
    if s is None:
        return 'None'
    if bytes is str or is_String(s):
        return s
    return str (s, 'utf-8')


def cmp(a, b):
    """
    Define cmp because it's no longer available in python3
    Works under python 2 as well
    """
    return (a > b) - (a < b)


def get_env_bool(env, name, default=False):
    """Get a value of env[name] converted to boolean. The value of env[name] is
    interpreted as follows: 'true', 'yes', 'y', 'on' (case insensitive) and
    anything convertible to int that yields non-zero integer are True values;
    '0', 'false', 'no', 'n' and 'off' (case insensitive) are False values. For
    all other cases, default value is returned.

    :Parameters:
        - `env`     - dict or dict-like object, a convainer with variables
        - `name`    - name of the variable in env to be returned
        - `default` - returned when env[name] does not exist or can't be converted to bool
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
        elif str(var).lower() in ('false', 'no', 'n', 'off'):
            return False
        else:
            return default


def get_os_env_bool(name, default=False):
    """Same as get_env_bool(os.environ, name, default)."""
    return get_env_bool(os.environ, name, default)

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
