"""scons.Node.FS

File system nodes.

These Nodes represent the canonical external objects that people think
of when they think of building software: files and directories.

This holds a "default_fs" variable that should be initialized with an FS
that can be used by scripts or modules looking for the canonical default.

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
from __future__ import print_function

__revision__ = "src/engine/SCons/Node/FS.py bee7caf9defd6e108fc2998a2520ddb36a967691 2019-12-17 02:07:09 bdeegan"

import fnmatch
import os
import re
import shutil
import stat
import sys
import time
import codecs
from itertools import chain

import SCons.Action
import SCons.Debug
from SCons.Debug import logInstanceCreation
import SCons.Errors
import SCons.Memoize
import SCons.Node
import SCons.Node.Alias
import SCons.Subst
import SCons.Util
import SCons.Warnings

from SCons.Debug import Trace

print_duplicate = 0

MD5_TIMESTAMP_DEBUG = False


def sconsign_none(node):
    raise NotImplementedError

def sconsign_dir(node):
    """Return the .sconsign file info for this directory,
    creating it first if necessary."""
    if not node._sconsign:
        import SCons.SConsign
        node._sconsign = SCons.SConsign.ForDirectory(node)
    return node._sconsign

_sconsign_map = {0 : sconsign_none,
                 1 : sconsign_dir}

class FileBuildInfoFileToCsigMappingError(Exception):
    pass

class EntryProxyAttributeError(AttributeError):
    """
    An AttributeError subclass for recording and displaying the name
    of the underlying Entry involved in an AttributeError exception.
    """
    def __init__(self, entry_proxy, attribute):
        AttributeError.__init__(self)
        self.entry_proxy = entry_proxy
        self.attribute = attribute
    def __str__(self):
        entry = self.entry_proxy.get()
        fmt = "%s instance %s has no attribute %s"
        return fmt % (entry.__class__.__name__,
                      repr(entry.name),
                      repr(self.attribute))

# The max_drift value:  by default, use a cached signature value for
# any file that's been untouched for more than two days.
default_max_drift = 2*24*60*60

#
# We stringify these file system Nodes a lot.  Turning a file system Node
# into a string is non-trivial, because the final string representation
# can depend on a lot of factors:  whether it's a derived target or not,
# whether it's linked to a repository or source directory, and whether
# there's duplication going on.  The normal technique for optimizing
# calculations like this is to memoize (cache) the string value, so you
# only have to do the calculation once.
#
# A number of the above factors, however, can be set after we've already
# been asked to return a string for a Node, because a Repository() or
# VariantDir() call or the like may not occur until later in SConscript
# files.  So this variable controls whether we bother trying to save
# string values for Nodes.  The wrapper interface can set this whenever
# they're done mucking with Repository and VariantDir and the other stuff,
# to let this module know it can start returning saved string values
# for Nodes.
#
Save_Strings = None

def save_strings(val):
    global Save_Strings
    Save_Strings = val

#
# Avoid unnecessary function calls by recording a Boolean value that
# tells us whether or not os.path.splitdrive() actually does anything
# on this system, and therefore whether we need to bother calling it
# when looking up path names in various methods below.
#

do_splitdrive = None
_my_splitdrive =None

def initialize_do_splitdrive():
    global do_splitdrive
    global has_unc
    drive, path = os.path.splitdrive('X:/foo')
    # splitunc is removed from python 3.7 and newer
    # so we can also just test if splitdrive works with UNC
    has_unc = (hasattr(os.path, 'splitunc')
        or os.path.splitdrive(r'\\split\drive\test')[0] == r'\\split\drive')

    do_splitdrive = not not drive or has_unc

    global _my_splitdrive
    if has_unc:
        def splitdrive(p):
            if p[1:2] == ':':
                return p[:2], p[2:]
            if p[0:2] == '//':
                # Note that we leave a leading slash in the path
                # because UNC paths are always absolute.
                return '//', p[1:]
            return '', p
    else:
        def splitdrive(p):
            if p[1:2] == ':':
                return p[:2], p[2:]
            return '', p
    _my_splitdrive = splitdrive

    # Keep some commonly used values in global variables to skip to
    # module look-up costs.
    global OS_SEP
    global UNC_PREFIX
    global os_sep_is_slash

    OS_SEP = os.sep
    UNC_PREFIX = OS_SEP + OS_SEP
    os_sep_is_slash = OS_SEP == '/'

initialize_do_splitdrive()

# Used to avoid invoking os.path.normpath if not necessary.
needs_normpath_check = re.compile(
    r'''
      # We need to renormalize the path if it contains any consecutive
      # '/' characters.
      .*// |

      # We need to renormalize the path if it contains a '..' directory.
      # Note that we check for all the following cases:
      #
      #    a) The path is a single '..'
      #    b) The path starts with '..'. E.g. '../' or '../moredirs'
      #       but we not match '..abc/'.
      #    c) The path ends with '..'. E.g. '/..' or 'dirs/..'
      #    d) The path contains a '..' in the middle.
      #       E.g. dirs/../moredirs

      (.*/)?\.\.(?:/|$) |

      # We need to renormalize the path if it contains a '.'
      # directory, but NOT if it is a single '.'  '/' characters. We
      # do not want to match a single '.' because this case is checked
      # for explicitly since this is common enough case.
      #
      # Note that we check for all the following cases:
      #
      #    a) We don't match a single '.'
      #    b) We match if the path starts with '.'. E.g. './' or
      #       './moredirs' but we not match '.abc/'.
      #    c) We match if the path ends with '.'. E.g. '/.' or
      #    'dirs/.'
      #    d) We match if the path contains a '.' in the middle.
      #       E.g. dirs/./moredirs

      \./|.*/\.(?:/|$)

    ''',
    re.VERBOSE
    )
needs_normpath_match = needs_normpath_check.match

#
# SCons.Action objects for interacting with the outside world.
#
# The Node.FS methods in this module should use these actions to
# create and/or remove files and directories; they should *not* use
# os.{link,symlink,unlink,mkdir}(), etc., directly.
#
# Using these SCons.Action objects ensures that descriptions of these
# external activities are properly displayed, that the displays are
# suppressed when the -s (silent) option is used, and (most importantly)
# the actions are disabled when the the -n option is used, in which case
# there should be *no* changes to the external file system(s)...
#

# For Now disable hard & softlinks for win32
# PY3 supports them, but the rest of SCons is not ready for this
# in some cases user permissions may be required.
# TODO: See if theres a reasonable way to enable using links on win32/64

if hasattr(os, 'link') and sys.platform != 'win32':
    def _hardlink_func(fs, src, dst):
        # If the source is a symlink, we can't just hard-link to it
        # because a relative symlink may point somewhere completely
        # different.  We must disambiguate the symlink and then
        # hard-link the final destination file.
        while fs.islink(src):
            link = fs.readlink(src)
            if not os.path.isabs(link):
                src = link
            else:
                src = os.path.join(os.path.dirname(src), link)
        fs.link(src, dst)
else:
    _hardlink_func = None

if hasattr(os, 'symlink') and sys.platform != 'win32':
    def _softlink_func(fs, src, dst):
        fs.symlink(src, dst)
else:
    _softlink_func = None

def _copy_func(fs, src, dest):
    shutil.copy2(src, dest)
    st = fs.stat(src)
    fs.chmod(dest, stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IWRITE)


Valid_Duplicates = ['hard-soft-copy', 'soft-hard-copy',
                    'hard-copy', 'soft-copy', 'copy']

Link_Funcs = [] # contains the callables of the specified duplication style

def set_duplicate(duplicate):
    # Fill in the Link_Funcs list according to the argument
    # (discarding those not available on the platform).

    # Set up the dictionary that maps the argument names to the
    # underlying implementations.  We do this inside this function,
    # not in the top-level module code, so that we can remap os.link
    # and os.symlink for testing purposes.
    link_dict = {
        'hard' : _hardlink_func,
        'soft' : _softlink_func,
        'copy' : _copy_func
    }

    if duplicate not in Valid_Duplicates:
        raise SCons.Errors.InternalError("The argument of set_duplicate "
                                           "should be in Valid_Duplicates")
    global Link_Funcs
    Link_Funcs = []
    for func in duplicate.split('-'):
        if link_dict[func]:
            Link_Funcs.append(link_dict[func])

def LinkFunc(target, source, env):
    """
    Relative paths cause problems with symbolic links, so
    we use absolute paths, which may be a problem for people
    who want to move their soft-linked src-trees around. Those
    people should use the 'hard-copy' mode, softlinks cannot be
    used for that; at least I have no idea how ...
    """
    src = source[0].get_abspath()
    dest = target[0].get_abspath()
    dir, file = os.path.split(dest)
    if dir and not target[0].fs.isdir(dir):
        os.makedirs(dir)
    if not Link_Funcs:
        # Set a default order of link functions.
        set_duplicate('hard-soft-copy')
    fs = source[0].fs
    # Now link the files with the previously specified order.
    for func in Link_Funcs:
        try:
            func(fs, src, dest)
            break
        except (IOError, OSError):
            # An OSError indicates something happened like a permissions
            # problem or an attempt to symlink across file-system
            # boundaries.  An IOError indicates something like the file
            # not existing.  In either case, keeping trying additional
            # functions in the list and only raise an error if the last
            # one failed.
            if func == Link_Funcs[-1]:
                # exception of the last link method (copy) are fatal
                raise
    return 0

Link = SCons.Action.Action(LinkFunc, None)
def LocalString(target, source, env):
    return 'Local copy of %s from %s' % (target[0], source[0])

LocalCopy = SCons.Action.Action(LinkFunc, LocalString)

def UnlinkFunc(target, source, env):
    t = target[0]
    t.fs.unlink(t.get_abspath())
    return 0

Unlink = SCons.Action.Action(UnlinkFunc, None)

def MkdirFunc(target, source, env):
    t = target[0]
    # This os.path.exists test looks redundant, but it's possible
    # when using Install() to install multiple dirs outside the
    # source tree to get a case where t.exists() is true but
    # the path does already exist, so this prevents spurious
    # build failures in that case. See test/Install/multi-dir.
    if not t.exists() and not os.path.exists(t.get_abspath()):
        t.fs.mkdir(t.get_abspath())
    return 0

Mkdir = SCons.Action.Action(MkdirFunc, None, presub=None)

MkdirBuilder = None

def get_MkdirBuilder():
    global MkdirBuilder
    if MkdirBuilder is None:
        import SCons.Builder
        import SCons.Defaults
        # "env" will get filled in by Executor.get_build_env()
        # calling SCons.Defaults.DefaultEnvironment() when necessary.
        MkdirBuilder = SCons.Builder.Builder(action = Mkdir,
                                             env = None,
                                             explain = None,
                                             is_explicit = None,
                                             target_scanner = SCons.Defaults.DirEntryScanner,
                                             name = "MkdirBuilder")
    return MkdirBuilder

class _Null(object):
    pass

_null = _Null()

# Cygwin's os.path.normcase pretends it's on a case-sensitive filesystem.
_is_cygwin = sys.platform == "cygwin"
if os.path.normcase("TeSt") == os.path.normpath("TeSt") and not _is_cygwin:
    def _my_normcase(x):
        return x
else:
    def _my_normcase(x):
        return x.upper()



class DiskChecker(object):
    def __init__(self, type, do, ignore):
        self.type = type
        self.do = do
        self.ignore = ignore
        self.func = do
    def __call__(self, *args, **kw):
        return self.func(*args, **kw)
    def set(self, list):
        if self.type in list:
            self.func = self.do
        else:
            self.func = self.ignore

def do_diskcheck_match(node, predicate, errorfmt):
    result = predicate()
    try:
        # If calling the predicate() cached a None value from stat(),
        # remove it so it doesn't interfere with later attempts to
        # build this Node as we walk the DAG.  (This isn't a great way
        # to do this, we're reaching into an interface that doesn't
        # really belong to us, but it's all about performance, so
        # for now we'll just document the dependency...)
        if node._memo['stat'] is None:
            del node._memo['stat']
    except (AttributeError, KeyError):
        pass
    if result:
        raise TypeError(errorfmt % node.get_abspath())

def ignore_diskcheck_match(node, predicate, errorfmt):
    pass



diskcheck_match = DiskChecker('match', do_diskcheck_match, ignore_diskcheck_match)

diskcheckers = [
    diskcheck_match,
]

def set_diskcheck(list):
    for dc in diskcheckers:
        dc.set(list)

def diskcheck_types():
    return [dc.type for dc in diskcheckers]



class EntryProxy(SCons.Util.Proxy):

    __str__ = SCons.Util.Delegate('__str__')

    # In PY3 if a class defines __eq__, then it must explicitly provide
    # __hash__.  Since SCons.Util.Proxy provides __eq__ we need the following
    # see: https://docs.python.org/3.1/reference/datamodel.html#object.__hash__
    __hash__ = SCons.Util.Delegate('__hash__')

    def __get_abspath(self):
        entry = self.get()
        return SCons.Subst.SpecialAttrWrapper(entry.get_abspath(),
                                             entry.name + "_abspath")

    def __get_filebase(self):
        name = self.get().name
        return SCons.Subst.SpecialAttrWrapper(SCons.Util.splitext(name)[0],
                                             name + "_filebase")

    def __get_suffix(self):
        name = self.get().name
        return SCons.Subst.SpecialAttrWrapper(SCons.Util.splitext(name)[1],
                                             name + "_suffix")

    def __get_file(self):
        name = self.get().name
        return SCons.Subst.SpecialAttrWrapper(name, name + "_file")

    def __get_base_path(self):
        """Return the file's directory and file name, with the
        suffix stripped."""
        entry = self.get()
        return SCons.Subst.SpecialAttrWrapper(SCons.Util.splitext(entry.get_path())[0],
                                             entry.name + "_base")

    def __get_posix_path(self):
        """Return the path with / as the path separator,
        regardless of platform."""
        if os_sep_is_slash:
            return self
        else:
            entry = self.get()
            r = entry.get_path().replace(OS_SEP, '/')
            return SCons.Subst.SpecialAttrWrapper(r, entry.name + "_posix")

    def __get_windows_path(self):
        r"""Return the path with \ as the path separator,
        regardless of platform."""
        if OS_SEP == '\\':
            return self
        else:
            entry = self.get()
            r = entry.get_path().replace(OS_SEP, '\\')
            return SCons.Subst.SpecialAttrWrapper(r, entry.name + "_windows")

    def __get_srcnode(self):
        return EntryProxy(self.get().srcnode())

    def __get_srcdir(self):
        """Returns the directory containing the source node linked to this
        node via VariantDir(), or the directory of this node if not linked."""
        return EntryProxy(self.get().srcnode().dir)

    def __get_rsrcnode(self):
        return EntryProxy(self.get().srcnode().rfile())

    def __get_rsrcdir(self):
        """Returns the directory containing the source node linked to this
        node via VariantDir(), or the directory of this node if not linked."""
        return EntryProxy(self.get().srcnode().rfile().dir)

    def __get_dir(self):
        return EntryProxy(self.get().dir)

    dictSpecialAttrs = { "base"     : __get_base_path,
                         "posix"    : __get_posix_path,
                         "windows"  : __get_windows_path,
                         "win32"    : __get_windows_path,
                         "srcpath"  : __get_srcnode,
                         "srcdir"   : __get_srcdir,
                         "dir"      : __get_dir,
                         "abspath"  : __get_abspath,
                         "filebase" : __get_filebase,
                         "suffix"   : __get_suffix,
                         "file"     : __get_file,
                         "rsrcpath" : __get_rsrcnode,
                         "rsrcdir"  : __get_rsrcdir,
                       }

    def __getattr__(self, name):
        # This is how we implement the "special" attributes
        # such as base, posix, srcdir, etc.
        try:
            attr_function = self.dictSpecialAttrs[name]
        except KeyError:
            try:
                attr = SCons.Util.Proxy.__getattr__(self, name)
            except AttributeError:
                # Raise our own AttributeError subclass with an
                # overridden __str__() method that identifies the
                # name of the entry that caused the exception.
                raise EntryProxyAttributeError(self, name)
            return attr
        else:
            return attr_function(self)


class Base(SCons.Node.Node):
    """A generic class for file system entries.  This class is for
    when we don't know yet whether the entry being looked up is a file
    or a directory.  Instances of this class can morph into either
    Dir or File objects by a later, more precise lookup.

    Note: this class does not define __cmp__ and __hash__ for
    efficiency reasons.  SCons does a lot of comparing of
    Node.FS.{Base,Entry,File,Dir} objects, so those operations must be
    as fast as possible, which means we want to use Python's built-in
    object identity comparisons.
    """

    __slots__ = ['name',
                 'fs',
                 '_abspath',
                 '_labspath',
                 '_path',
                 '_tpath',
                 '_path_elements',
                 'dir',
                 'cwd',
                 'duplicate',
                 '_local',
                 'sbuilder',
                 '_proxy',
                 '_func_sconsign']

    def __init__(self, name, directory, fs):
        """Initialize a generic Node.FS.Base object.

        Call the superclass initialization, take care of setting up
        our relative and absolute paths, identify our parent
        directory, and indicate that this node should use
        signatures."""

        if SCons.Debug.track_instances: logInstanceCreation(self, 'Node.FS.Base')
        SCons.Node.Node.__init__(self)

        # Filenames and paths are probably reused and are intern'ed to save some memory.
        # Filename with extension as it was specified when the object was
        # created; to obtain filesystem path, use Python str() function
        self.name = SCons.Util.silent_intern(name)
        self.fs = fs #: Reference to parent Node.FS object

        assert directory, "A directory must be provided"

        self._abspath = None
        self._labspath = None
        self._path = None
        self._tpath = None
        self._path_elements = None

        self.dir = directory
        self.cwd = None # will hold the SConscript directory for target nodes
        self.duplicate = directory.duplicate
        self.changed_since_last_build = 2
        self._func_sconsign = 0
        self._func_exists = 2
        self._func_rexists = 2
        self._func_get_contents = 0
        self._func_target_from_source = 1
        self.store_info = 1

    def str_for_display(self):
        return '"' + self.__str__() + '"'

    def must_be_same(self, klass):
        """
        This node, which already existed, is being looked up as the
        specified klass.  Raise an exception if it isn't.
        """
        if isinstance(self, klass) or klass is Entry:
            return
        raise TypeError("Tried to lookup %s '%s' as a %s." %\
              (self.__class__.__name__, self.get_internal_path(), klass.__name__))

    def get_dir(self):
        return self.dir

    def get_suffix(self):
        return SCons.Util.splitext(self.name)[1]

    def rfile(self):
        return self

    def __getattr__(self, attr):
        """ Together with the node_bwcomp dict defined below,
            this method provides a simple backward compatibility
            layer for the Node attributes 'abspath', 'labspath',
            'path', 'tpath', 'suffix' and 'path_elements'. These Node
            attributes used to be directly available in v2.3 and earlier, but
            have been replaced by getter methods that initialize the
            single variables lazily when required, in order to save memory.
            The redirection to the getters lets older Tools and
            SConstruct continue to work without any additional changes,
            fully transparent to the user.
            Note, that __getattr__ is only called as fallback when the
            requested attribute can't be found, so there should be no
            speed performance penalty involved for standard builds.
        """
        if attr in node_bwcomp:
            return node_bwcomp[attr](self)

        raise AttributeError("%r object has no attribute %r" %
                         (self.__class__, attr))

    def __str__(self):
        """A Node.FS.Base object's string representation is its path
        name."""
        global Save_Strings
        if Save_Strings:
            return self._save_str()
        return self._get_str()

    def __lt__(self, other):
        """ less than operator used by sorting on py3"""
        return str(self) < str(other)

    @SCons.Memoize.CountMethodCall
    def _save_str(self):
        try:
            return self._memo['_save_str']
        except KeyError:
            pass
        result = SCons.Util.silent_intern(self._get_str())
        self._memo['_save_str'] = result
        return result

    def _get_str(self):
        global Save_Strings
        if self.duplicate or self.is_derived():
            return self.get_path()
        srcnode = self.srcnode()
        if srcnode.stat() is None and self.stat() is not None:
            result = self.get_path()
        else:
            result = srcnode.get_path()
        if not Save_Strings:
            # We're not at the point where we're saving the string
            # representations of FS Nodes (because we haven't finished
            # reading the SConscript files and need to have str() return
            # things relative to them).  That also means we can't yet
            # cache values returned (or not returned) by stat(), since
            # Python code in the SConscript files might still create
            # or otherwise affect the on-disk file.  So get rid of the
            # values that the underlying stat() method saved.
            try: del self._memo['stat']
            except KeyError: pass
            if self is not srcnode:
                try: del srcnode._memo['stat']
                except KeyError: pass
        return result

    rstr = __str__

    @SCons.Memoize.CountMethodCall
    def stat(self):
        try:
            return self._memo['stat']
        except KeyError:
            pass
        try:
            result = self.fs.stat(self.get_abspath())
        except os.error:
            result = None

        self._memo['stat'] = result
        return result

    def exists(self):
        return SCons.Node._exists_map[self._func_exists](self)

    def rexists(self):
        return SCons.Node._rexists_map[self._func_rexists](self)

    def getmtime(self):
        st = self.stat()
        if st:
            return st[stat.ST_MTIME]
        else:
            return None

    def getsize(self):
        st = self.stat()
        if st:
            return st[stat.ST_SIZE]
        else:
            return None

    def isdir(self):
        st = self.stat()
        return st is not None and stat.S_ISDIR(st[stat.ST_MODE])

    def isfile(self):
        st = self.stat()
        return st is not None and stat.S_ISREG(st[stat.ST_MODE])

    if hasattr(os, 'symlink'):
        def islink(self):
            try: st = self.fs.lstat(self.get_abspath())
            except os.error: return 0
            return stat.S_ISLNK(st[stat.ST_MODE])
    else:
        def islink(self):
            return 0                    # no symlinks

    def is_under(self, dir):
        if self is dir:
            return 1
        else:
            return self.dir.is_under(dir)

    def set_local(self):
        self._local = 1

    def srcnode(self):
        """If this node is in a build path, return the node
        corresponding to its source file.  Otherwise, return
        ourself.
        """
        srcdir_list = self.dir.srcdir_list()
        if srcdir_list:
            srcnode = srcdir_list[0].Entry(self.name)
            srcnode.must_be_same(self.__class__)
            return srcnode
        return self

    def get_path(self, dir=None):
        """Return path relative to the current working directory of the
        Node.FS.Base object that owns us."""
        if not dir:
            dir = self.fs.getcwd()
        if self == dir:
            return '.'
        path_elems = self.get_path_elements()
        pathname = ''
        try: i = path_elems.index(dir)
        except ValueError:
            for p in path_elems[:-1]:
                pathname += p.dirname
        else:
            for p in path_elems[i+1:-1]:
                pathname += p.dirname
        return pathname + path_elems[-1].name

    def set_src_builder(self, builder):
        """Set the source code builder for this node."""
        self.sbuilder = builder
        if not self.has_builder():
            self.builder_set(builder)

    def src_builder(self):
        """Fetch the source code builder for this node.

        If there isn't one, we cache the source code builder specified
        for the directory (which in turn will cache the value from its
        parent directory, and so on up to the file system root).
        """
        try:
            scb = self.sbuilder
        except AttributeError:
            scb = self.dir.src_builder()
            self.sbuilder = scb
        return scb

    def get_abspath(self):
        """Get the absolute path of the file."""
        return self.dir.entry_abspath(self.name)

    def get_labspath(self):
        """Get the absolute path of the file."""
        return self.dir.entry_labspath(self.name)

    def get_internal_path(self):
        if self.dir._path == '.':
            return self.name
        else:
            return self.dir.entry_path(self.name)

    def get_tpath(self):
        if self.dir._tpath == '.':
            return self.name
        else:
            return self.dir.entry_tpath(self.name)

    def get_path_elements(self):
        return self.dir._path_elements + [self]

    def for_signature(self):
        # Return just our name.  Even an absolute path would not work,
        # because that can change thanks to symlinks or remapped network
        # paths.
        return self.name

    def get_subst_proxy(self):
        try:
            return self._proxy
        except AttributeError:
            ret = EntryProxy(self)
            self._proxy = ret
            return ret

    def target_from_source(self, prefix, suffix, splitext=SCons.Util.splitext):
        """

        Generates a target entry that corresponds to this entry (usually
        a source file) with the specified prefix and suffix.

        Note that this method can be overridden dynamically for generated
        files that need different behavior.  See Tool/swig.py for
        an example.
        """
        return SCons.Node._target_from_source_map[self._func_target_from_source](self, prefix, suffix, splitext)

    def _Rfindalldirs_key(self, pathlist):
        return pathlist

    @SCons.Memoize.CountDictCall(_Rfindalldirs_key)
    def Rfindalldirs(self, pathlist):
        """
        Return all of the directories for a given path list, including
        corresponding "backing" directories in any repositories.

        The Node lookups are relative to this Node (typically a
        directory), so memoizing result saves cycles from looking
        up the same path for each target in a given directory.
        """
        try:
            memo_dict = self._memo['Rfindalldirs']
        except KeyError:
            memo_dict = {}
            self._memo['Rfindalldirs'] = memo_dict
        else:
            try:
                return memo_dict[pathlist]
            except KeyError:
                pass

        create_dir_relative_to_self = self.Dir
        result = []
        for path in pathlist:
            if isinstance(path, SCons.Node.Node):
                result.append(path)
            else:
                dir = create_dir_relative_to_self(path)
                result.extend(dir.get_all_rdirs())

        memo_dict[pathlist] = result

        return result

    def RDirs(self, pathlist):
        """Search for a list of directories in the Repository list."""
        cwd = self.cwd or self.fs._cwd
        return cwd.Rfindalldirs(pathlist)

    @SCons.Memoize.CountMethodCall
    def rentry(self):
        try:
            return self._memo['rentry']
        except KeyError:
            pass
        result = self
        if not self.exists():
            norm_name = _my_normcase(self.name)
            for dir in self.dir.get_all_rdirs():
                try:
                    node = dir.entries[norm_name]
                except KeyError:
                    if dir.entry_exists_on_disk(self.name):
                        result = dir.Entry(self.name)
                        break
        self._memo['rentry'] = result
        return result

    def _glob1(self, pattern, ondisk=True, source=False, strings=False):
        return []

# Dict that provides a simple backward compatibility
# layer for the Node attributes 'abspath', 'labspath',
# 'path', 'tpath' and 'path_elements'.
# @see Base.__getattr__ above
node_bwcomp = {'abspath' : Base.get_abspath,
               'labspath' : Base.get_labspath,
               'path' : Base.get_internal_path,
               'tpath' : Base.get_tpath,
               'path_elements' : Base.get_path_elements,
               'suffix' : Base.get_suffix}

class Entry(Base):
    """This is the class for generic Node.FS entries--that is, things
    that could be a File or a Dir, but we're just not sure yet.
    Consequently, the methods in this class really exist just to
    transform their associated object into the right class when the
    time comes, and then call the same-named method in the transformed
    class."""

    __slots__ = ['scanner_paths',
                 'cachedir_csig',
                 'cachesig',
                 'repositories',
                 'srcdir',
                 'entries',
                 'searched',
                 '_sconsign',
                 'variant_dirs',
                 'root',
                 'dirname',
                 'on_disk_entries',
                 'released_target_info',
                 'contentsig']

    def __init__(self, name, directory, fs):
        Base.__init__(self, name, directory, fs)
        self._func_exists = 3
        self._func_get_contents = 1

    def diskcheck_match(self):
        pass

    def disambiguate(self, must_exist=None):
        """
        """
        if self.isfile():
            self.__class__ = File
            self._morph()
            self.clear()
        elif self.isdir():
            self.__class__ = Dir
            self._morph()
        else:
            # There was nothing on-disk at this location, so look in
            # the src directory.
            #
            # We can't just use self.srcnode() straight away because
            # that would create an actual Node for this file in the src
            # directory, and there might not be one.  Instead, use the
            # dir_on_disk() method to see if there's something on-disk
            # with that name, in which case we can go ahead and call
            # self.srcnode() to create the right type of entry.
            srcdir = self.dir.srcnode()
            if srcdir != self.dir and \
               srcdir.entry_exists_on_disk(self.name) and \
               self.srcnode().isdir():
                self.__class__ = Dir
                self._morph()
            elif must_exist:
                msg = "No such file or directory: '%s'" % self.get_abspath()
                raise SCons.Errors.UserError(msg)
            else:
                self.__class__ = File
                self._morph()
                self.clear()
        return self

    def rfile(self):
        """We're a generic Entry, but the caller is actually looking for
        a File at this point, so morph into one."""
        self.__class__ = File
        self._morph()
        self.clear()
        return File.rfile(self)

    def scanner_key(self):
        return self.get_suffix()

    def get_contents(self):
        """Fetch the contents of the entry.  Returns the exact binary
        contents of the file."""
        return SCons.Node._get_contents_map[self._func_get_contents](self)

    def get_text_contents(self):
        """Fetch the decoded text contents of a Unicode encoded Entry.

        Since this should return the text contents from the file
        system, we check to see into what sort of subclass we should
        morph this Entry."""
        try:
            self = self.disambiguate(must_exist=1)
        except SCons.Errors.UserError:
            # There was nothing on disk with which to disambiguate
            # this entry.  Leave it as an Entry, but return a null
            # string so calls to get_text_contents() in emitters and
            # the like (e.g. in qt.py) don't have to disambiguate by
            # hand or catch the exception.
            return ''
        else:
            return self.get_text_contents()

    def must_be_same(self, klass):
        """Called to make sure a Node is a Dir.  Since we're an
        Entry, we can morph into one."""
        if self.__class__ is not klass:
            self.__class__ = klass
            self._morph()
            self.clear()

    # The following methods can get called before the Taskmaster has
    # had a chance to call disambiguate() directly to see if this Entry
    # should really be a Dir or a File.  We therefore use these to call
    # disambiguate() transparently (from our caller's point of view).
    #
    # Right now, this minimal set of methods has been derived by just
    # looking at some of the methods that will obviously be called early
    # in any of the various Taskmasters' calling sequences, and then
    # empirically figuring out which additional methods are necessary
    # to make various tests pass.

    def exists(self):
        return SCons.Node._exists_map[self._func_exists](self)

    def rel_path(self, other):
        d = self.disambiguate()
        if d.__class__ is Entry:
            raise Exception("rel_path() could not disambiguate File/Dir")
        return d.rel_path(other)

    def new_ninfo(self):
        return self.disambiguate().new_ninfo()

    def _glob1(self, pattern, ondisk=True, source=False, strings=False):
        return self.disambiguate()._glob1(pattern, ondisk, source, strings)

    def get_subst_proxy(self):
        return self.disambiguate().get_subst_proxy()

# This is for later so we can differentiate between Entry the class and Entry
# the method of the FS class.
_classEntry = Entry


class LocalFS(object):
    """
    This class implements an abstraction layer for operations involving
    a local file system.  Essentially, this wraps any function in
    the os, os.path or shutil modules that we use to actually go do
    anything with or to the local file system.

    Note that there's a very good chance we'll refactor this part of
    the architecture in some way as we really implement the interface(s)
    for remote file system Nodes.  For example, the right architecture
    might be to have this be a subclass instead of a base class.
    Nevertheless, we're using this as a first step in that direction.

    We're not using chdir() yet because the calling subclass method
    needs to use os.chdir() directly to avoid recursion.  Will we
    really need this one?
    """
    #def chdir(self, path):
    #    return os.chdir(path)
    def chmod(self, path, mode):
        return os.chmod(path, mode)
    def copy(self, src, dst):
        return shutil.copy(src, dst)
    def copy2(self, src, dst):
        return shutil.copy2(src, dst)
    def exists(self, path):
        return os.path.exists(path)
    def getmtime(self, path):
        return os.path.getmtime(path)
    def getsize(self, path):
        return os.path.getsize(path)
    def isdir(self, path):
        return os.path.isdir(path)
    def isfile(self, path):
        return os.path.isfile(path)
    def link(self, src, dst):
        return os.link(src, dst)
    def lstat(self, path):
        return os.lstat(path)
    def listdir(self, path):
        return os.listdir(path)
    def makedirs(self, path):
        return os.makedirs(path)
    def mkdir(self, path):
        return os.mkdir(path)
    def rename(self, old, new):
        return os.rename(old, new)
    def stat(self, path):
        return os.stat(path)
    def symlink(self, src, dst):
        return os.symlink(src, dst)
    def open(self, path):
        return open(path)
    def unlink(self, path):
        return os.unlink(path)

    if hasattr(os, 'symlink'):
        def islink(self, path):
            return os.path.islink(path)
    else:
        def islink(self, path):
            return 0                    # no symlinks

    if hasattr(os, 'readlink'):
        def readlink(self, file):
            return os.readlink(file)
    else:
        def readlink(self, file):
            return ''


class FS(LocalFS):

    def __init__(self, path = None):
        """Initialize the Node.FS subsystem.

        The supplied path is the top of the source tree, where we
        expect to find the top-level build file.  If no path is
        supplied, the current directory is the default.

        The path argument must be a valid absolute path.
        """
        if SCons.Debug.track_instances: logInstanceCreation(self, 'Node.FS')

        self._memo = {}

        self.Root = {}
        self.SConstruct_dir = None
        self.max_drift = default_max_drift

        self.Top = None
        if path is None:
            self.pathTop = os.getcwd()
        else:
            self.pathTop = path
        self.defaultDrive = _my_normcase(_my_splitdrive(self.pathTop)[0])

        self.Top = self.Dir(self.pathTop)
        self.Top._path = '.'
        self.Top._tpath = '.'
        self._cwd = self.Top

        DirNodeInfo.fs = self
        FileNodeInfo.fs = self

    def set_SConstruct_dir(self, dir):
        self.SConstruct_dir = dir

    def get_max_drift(self):
        return self.max_drift

    def set_max_drift(self, max_drift):
        self.max_drift = max_drift

    def getcwd(self):
        if hasattr(self, "_cwd"):
            return self._cwd
        else:
            return "<no cwd>"

    def chdir(self, dir, change_os_dir=0):
        """Change the current working directory for lookups.
        If change_os_dir is true, we will also change the "real" cwd
        to match.
        """
        curr=self._cwd
        try:
            if dir is not None:
                self._cwd = dir
                if change_os_dir:
                    os.chdir(dir.get_abspath())
        except OSError:
            self._cwd = curr
            raise

    def get_root(self, drive):
        """
        Returns the root directory for the specified drive, creating
        it if necessary.
        """
        drive = _my_normcase(drive)
        try:
            return self.Root[drive]
        except KeyError:
            root = RootDir(drive, self)
            self.Root[drive] = root
            if not drive:
                self.Root[self.defaultDrive] = root
            elif drive == self.defaultDrive:
                self.Root[''] = root
            return root

    def _lookup(self, p, directory, fsclass, create=1):
        """
        The generic entry point for Node lookup with user-supplied data.

        This translates arbitrary input into a canonical Node.FS object
        of the specified fsclass.  The general approach for strings is
        to turn it into a fully normalized absolute path and then call
        the root directory's lookup_abs() method for the heavy lifting.

        If the path name begins with '#', it is unconditionally
        interpreted relative to the top-level directory of this FS.  '#'
        is treated as a synonym for the top-level SConstruct directory,
        much like '~' is treated as a synonym for the user's home
        directory in a UNIX shell.  So both '#foo' and '#/foo' refer
        to the 'foo' subdirectory underneath the top-level SConstruct
        directory.

        If the path name is relative, then the path is looked up relative
        to the specified directory, or the current directory (self._cwd,
        typically the SConscript directory) if the specified directory
        is None.
        """
        if isinstance(p, Base):
            # It's already a Node.FS object.  Make sure it's the right
            # class and return.
            p.must_be_same(fsclass)
            return p
        # str(p) in case it's something like a proxy object
        p = str(p)

        if not os_sep_is_slash:
            p = p.replace(OS_SEP, '/')

        if p[0:1] == '#':
            # There was an initial '#', so we strip it and override
            # whatever directory they may have specified with the
            # top-level SConstruct directory.
            p = p[1:]
            directory = self.Top

            # There might be a drive letter following the
            # '#'. Although it is not described in the SCons man page,
            # the regression test suite explicitly tests for that
            # syntax. It seems to mean the following thing:
            #
            #   Assuming the the SCons top dir is in C:/xxx/yyy,
            #   '#X:/toto' means X:/xxx/yyy/toto.
            #
            # i.e. it assumes that the X: drive has a directory
            # structure similar to the one found on drive C:.
            if do_splitdrive:
                drive, p = _my_splitdrive(p)
                if drive:
                    root = self.get_root(drive)
                else:
                    root = directory.root
            else:
                root = directory.root

            # We can only strip trailing after splitting the drive
            # since the drive might the UNC '//' prefix.
            p = p.strip('/')

            needs_normpath = needs_normpath_match(p)

            # The path is relative to the top-level SCons directory.
            if p in ('', '.'):
                p = directory.get_labspath()
            else:
                p = directory.get_labspath() + '/' + p
        else:
            if do_splitdrive:
                drive, p = _my_splitdrive(p)
                if drive and not p:
                    # This causes a naked drive letter to be treated
                    # as a synonym for the root directory on that
                    # drive.
                    p = '/'
            else:
                drive = ''

            # We can only strip trailing '/' since the drive might the
            # UNC '//' prefix.
            if p != '/':
                p = p.rstrip('/')

            needs_normpath = needs_normpath_match(p)

            if p[0:1] == '/':
                # Absolute path
                root = self.get_root(drive)
            else:
                # This is a relative lookup or to the current directory
                # (the path name is not absolute).  Add the string to the
                # appropriate directory lookup path, after which the whole
                # thing gets normalized.
                if directory:
                    if not isinstance(directory, Dir):
                        directory = self.Dir(directory)
                else:
                    directory = self._cwd

                if p in ('', '.'):
                    p = directory.get_labspath()
                else:
                    p = directory.get_labspath() + '/' + p

                if drive:
                    root = self.get_root(drive)
                else:
                    root = directory.root

        if needs_normpath is not None:
            # Normalize a pathname. Will return the same result for
            # equivalent paths.
            #
            # We take advantage of the fact that we have an absolute
            # path here for sure. In addition, we know that the
            # components of lookup path are separated by slashes at
            # this point. Because of this, this code is about 2X
            # faster than calling os.path.normpath() followed by
            # replacing os.sep with '/' again.
            ins = p.split('/')[1:]
            outs = []
            for d in ins:
                if d == '..':
                    try:
                        outs.pop()
                    except IndexError:
                        pass
                elif d not in ('', '.'):
                    outs.append(d)
            p = '/' + '/'.join(outs)

        return root._lookup_abs(p, fsclass, create)

    def Entry(self, name, directory = None, create = 1):
        """Look up or create a generic Entry node with the specified name.
        If the name is a relative path (begins with ./, ../, or a file
        name), then it is looked up relative to the supplied directory
        node, or to the top level directory of the FS (supplied at
        construction time) if no directory is supplied.
        """
        return self._lookup(name, directory, Entry, create)

    def File(self, name, directory = None, create = 1):
        """Look up or create a File node with the specified name.  If
        the name is a relative path (begins with ./, ../, or a file name),
        then it is looked up relative to the supplied directory node,
        or to the top level directory of the FS (supplied at construction
        time) if no directory is supplied.

        This method will raise TypeError if a directory is found at the
        specified path.
        """
        return self._lookup(name, directory, File, create)

    def Dir(self, name, directory = None, create = True):
        """Look up or create a Dir node with the specified name.  If
        the name is a relative path (begins with ./, ../, or a file name),
        then it is looked up relative to the supplied directory node,
        or to the top level directory of the FS (supplied at construction
        time) if no directory is supplied.

        This method will raise TypeError if a normal file is found at the
        specified path.
        """
        return self._lookup(name, directory, Dir, create)

    def VariantDir(self, variant_dir, src_dir, duplicate=1):
        """Link the supplied variant directory to the source directory
        for purposes of building files."""

        if not isinstance(src_dir, SCons.Node.Node):
            src_dir = self.Dir(src_dir)
        if not isinstance(variant_dir, SCons.Node.Node):
            variant_dir = self.Dir(variant_dir)
        if src_dir.is_under(variant_dir):
            raise SCons.Errors.UserError("Source directory cannot be under variant directory.")
        if variant_dir.srcdir:
            if variant_dir.srcdir == src_dir:
                return # We already did this.
            raise SCons.Errors.UserError("'%s' already has a source directory: '%s'."%(variant_dir, variant_dir.srcdir))
        variant_dir.link(src_dir, duplicate)

    def Repository(self, *dirs):
        """Specify Repository directories to search."""
        for d in dirs:
            if not isinstance(d, SCons.Node.Node):
                d = self.Dir(d)
            self.Top.addRepository(d)

    def PyPackageDir(self, modulename):
        r"""Locate the directory of a given python module name

        For example scons might resolve to
        Windows: C:\Python27\Lib\site-packages\scons-2.5.1
        Linux: /usr/lib/scons

        This can be useful when we want to determine a toolpath based on a python module name"""

        dirpath = ''
        if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] in (0,1,2,3,4)):
            # Python2 Code
            import imp
            splitname = modulename.split('.')
            srchpths = sys.path
            for item in splitname:
                file, path, desc = imp.find_module(item, srchpths)
                if file is not None:
                    path = os.path.dirname(path)
                srchpths = [path]
            dirpath = path
        else:
            # Python3 Code
            import importlib.util
            modspec = importlib.util.find_spec(modulename)
            dirpath = os.path.dirname(modspec.origin)
        return self._lookup(dirpath, None, Dir, True)


    def variant_dir_target_climb(self, orig, dir, tail):
        """Create targets in corresponding variant directories

        Climb the directory tree, and look up path names
        relative to any linked variant directories we find.

        Even though this loops and walks up the tree, we don't memoize
        the return value because this is really only used to process
        the command-line targets.
        """
        targets = []
        message = None
        fmt = "building associated VariantDir targets: %s"
        start_dir = dir
        while dir:
            for bd in dir.variant_dirs:
                if start_dir.is_under(bd):
                    # If already in the build-dir location, don't reflect
                    return [orig], fmt % str(orig)
                p = os.path.join(bd._path, *tail)
                targets.append(self.Entry(p))
            tail = [dir.name] + tail
            dir = dir.up()
        if targets:
            message = fmt % ' '.join(map(str, targets))
        return targets, message

    def Glob(self, pathname, ondisk=True, source=True, strings=False, exclude=None, cwd=None):
        """
        Globs

        This is mainly a shim layer
        """
        if cwd is None:
            cwd = self.getcwd()
        return cwd.glob(pathname, ondisk, source, strings, exclude)

class DirNodeInfo(SCons.Node.NodeInfoBase):
    __slots__ = ()
    # This should get reset by the FS initialization.
    current_version_id = 2

    fs = None

    def str_to_node(self, s):
        top = self.fs.Top
        root = top.root
        if do_splitdrive:
            drive, s = _my_splitdrive(s)
            if drive:
                root = self.fs.get_root(drive)
        if not os.path.isabs(s):
            s = top.get_labspath() + '/' + s
        return root._lookup_abs(s, Entry)

class DirBuildInfo(SCons.Node.BuildInfoBase):
    __slots__ = ()
    current_version_id = 2

glob_magic_check = re.compile('[*?[]')

def has_glob_magic(s):
    return glob_magic_check.search(s) is not None

class Dir(Base):
    """A class for directories in a file system.
    """

    __slots__ = ['scanner_paths',
                 'cachedir_csig',
                 'cachesig',
                 'repositories',
                 'srcdir',
                 'entries',
                 'searched',
                 '_sconsign',
                 'variant_dirs',
                 'root',
                 'dirname',
                 'on_disk_entries',
                 'released_target_info',
                 'contentsig']

    NodeInfo = DirNodeInfo
    BuildInfo = DirBuildInfo

    def __init__(self, name, directory, fs):
        if SCons.Debug.track_instances: logInstanceCreation(self, 'Node.FS.Dir')
        Base.__init__(self, name, directory, fs)
        self._morph()

    def _morph(self):
        """Turn a file system Node (either a freshly initialized directory
        object or a separate Entry object) into a proper directory object.

        Set up this directory's entries and hook it into the file
        system tree.  Specify that directories (this Node) don't use
        signatures for calculating whether they're current.
        """

        self.repositories = []
        self.srcdir = None

        self.entries = {}
        self.entries['.'] = self
        self.entries['..'] = self.dir
        self.cwd = self
        self.searched = 0
        self._sconsign = None
        self.variant_dirs = []
        self.root = self.dir.root
        self.changed_since_last_build = 3
        self._func_sconsign = 1
        self._func_exists = 2
        self._func_get_contents = 2

        self._abspath = SCons.Util.silent_intern(self.dir.entry_abspath(self.name))
        self._labspath = SCons.Util.silent_intern(self.dir.entry_labspath(self.name))
        if self.dir._path == '.':
            self._path = SCons.Util.silent_intern(self.name)
        else:
            self._path = SCons.Util.silent_intern(self.dir.entry_path(self.name))
        if self.dir._tpath == '.':
            self._tpath = SCons.Util.silent_intern(self.name)
        else:
            self._tpath = SCons.Util.silent_intern(self.dir.entry_tpath(self.name))
        self._path_elements = self.dir._path_elements + [self]

        # For directories, we make a difference between the directory
        # 'name' and the directory 'dirname'. The 'name' attribute is
        # used when we need to print the 'name' of the directory or
        # when we it is used as the last part of a path. The 'dirname'
        # is used when the directory is not the last element of the
        # path. The main reason for making that distinction is that
        # for RoorDir's the dirname can not be easily inferred from
        # the name. For example, we have to add a '/' after a drive
        # letter but not after a UNC path prefix ('//').
        self.dirname = self.name + OS_SEP

        # Don't just reset the executor, replace its action list,
        # because it might have some pre-or post-actions that need to
        # be preserved.
        #
        # But don't reset the executor if there is a non-null executor
        # attached already. The existing executor might have other
        # targets, in which case replacing the action list with a
        # Mkdir action is a big mistake.
        if not hasattr(self, 'executor'):
            self.builder = get_MkdirBuilder()
            self.get_executor().set_action_list(self.builder.action)
        else:
            # Prepend MkdirBuilder action to existing action list
            l = self.get_executor().action_list
            a = get_MkdirBuilder().action
            l.insert(0, a)
            self.get_executor().set_action_list(l)

    def diskcheck_match(self):
        # Nuitka: This check breaks with symlinks on Windows and Python2
        if os.name == "nt" and str is bytes:
            return

        diskcheck_match(self, self.isfile,
                        "File %s found where directory expected.")

    def __clearRepositoryCache(self, duplicate=None):
        """Called when we change the repository(ies) for a directory.
        This clears any cached information that is invalidated by changing
        the repository."""

        for node in list(self.entries.values()):
            if node != self.dir:
                if node != self and isinstance(node, Dir):
                    node.__clearRepositoryCache(duplicate)
                else:
                    node.clear()
                    try:
                        del node._srcreps
                    except AttributeError:
                        pass
                    if duplicate is not None:
                        node.duplicate=duplicate

    def __resetDuplicate(self, node):
        if node != self:
            node.duplicate = node.get_dir().duplicate

    def Entry(self, name):
        """
        Looks up or creates an entry node named 'name' relative to
        this directory.
        """
        return self.fs.Entry(name, self)

    def Dir(self, name, create=True):
        """
        Looks up or creates a directory node named 'name' relative to
        this directory.
        """
        return self.fs.Dir(name, self, create)

    def File(self, name):
        """
        Looks up or creates a file node named 'name' relative to
        this directory.
        """
        return self.fs.File(name, self)

    def link(self, srcdir, duplicate):
        """Set this directory as the variant directory for the
        supplied source directory."""
        self.srcdir = srcdir
        self.duplicate = duplicate
        self.__clearRepositoryCache(duplicate)
        srcdir.variant_dirs.append(self)

    def getRepositories(self):
        """Returns a list of repositories for this directory.
        """
        if self.srcdir and not self.duplicate:
            return self.srcdir.get_all_rdirs() + self.repositories
        return self.repositories

    @SCons.Memoize.CountMethodCall
    def get_all_rdirs(self):
        try:
            return list(self._memo['get_all_rdirs'])
        except KeyError:
            pass

        result = [self]
        fname = '.'
        dir = self
        while dir:
            for rep in dir.getRepositories():
                result.append(rep.Dir(fname))
            if fname == '.':
                fname = dir.name
            else:
                fname = dir.name + OS_SEP + fname
            dir = dir.up()

        self._memo['get_all_rdirs'] = list(result)

        return result

    def addRepository(self, dir):
        if dir != self and dir not in self.repositories:
            self.repositories.append(dir)
            dir._tpath = '.'
            self.__clearRepositoryCache()

    def up(self):
        return self.dir

    def _rel_path_key(self, other):
        return str(other)

    @SCons.Memoize.CountDictCall(_rel_path_key)
    def rel_path(self, other):
        """Return a path to "other" relative to this directory.
        """

        # This complicated and expensive method, which constructs relative
        # paths between arbitrary Node.FS objects, is no longer used
        # by SCons itself.  It was introduced to store dependency paths
        # in .sconsign files relative to the target, but that ended up
        # being significantly inefficient.
        #
        # We're continuing to support the method because some SConstruct
        # files out there started using it when it was available, and
        # we're all about backwards compatibility..

        try:
            memo_dict = self._memo['rel_path']
        except KeyError:
            memo_dict = {}
            self._memo['rel_path'] = memo_dict
        else:
            try:
                return memo_dict[other]
            except KeyError:
                pass

        if self is other:
            result = '.'

        elif other not in self._path_elements:
            try:
                other_dir = other.get_dir()
            except AttributeError:
                result = str(other)
            else:
                if other_dir is None:
                    result = other.name
                else:
                    dir_rel_path = self.rel_path(other_dir)
                    if dir_rel_path == '.':
                        result = other.name
                    else:
                        result = dir_rel_path + OS_SEP + other.name
        else:
            i = self._path_elements.index(other) + 1

            path_elems = ['..'] * (len(self._path_elements) - i) \
                         + [n.name for n in other._path_elements[i:]]

            result = OS_SEP.join(path_elems)

        memo_dict[other] = result

        return result

    def get_env_scanner(self, env, kw={}):
        import SCons.Defaults
        return SCons.Defaults.DirEntryScanner

    def get_target_scanner(self):
        import SCons.Defaults
        return SCons.Defaults.DirEntryScanner

    def get_found_includes(self, env, scanner, path):
        """Return this directory's implicit dependencies.

        We don't bother caching the results because the scan typically
        shouldn't be requested more than once (as opposed to scanning
        .h file contents, which can be requested as many times as the
        files is #included by other files).
        """
        if not scanner:
            return []
        # Clear cached info for this Dir.  If we already visited this
        # directory on our walk down the tree (because we didn't know at
        # that point it was being used as the source for another Node)
        # then we may have calculated build signature before realizing
        # we had to scan the disk.  Now that we have to, though, we need
        # to invalidate the old calculated signature so that any node
        # dependent on our directory structure gets one that includes
        # info about everything on disk.
        self.clear()
        return scanner(self, env, path)

    #
    # Taskmaster interface subsystem
    #

    def prepare(self):
        pass

    def build(self, **kw):
        """A null "builder" for directories."""
        global MkdirBuilder
        if self.builder is not MkdirBuilder:
            SCons.Node.Node.build(self, **kw)

    #
    #
    #

    def _create(self):
        """Create this directory, silently and without worrying about
        whether the builder is the default or not."""
        listDirs = []
        parent = self
        while parent:
            if parent.exists():
                break
            listDirs.append(parent)
            p = parent.up()
            if p is None:
                # Don't use while: - else: for this condition because
                # if so, then parent is None and has no .path attribute.
                raise SCons.Errors.StopError(parent._path)
            parent = p
        listDirs.reverse()
        for dirnode in listDirs:
            try:
                # Don't call dirnode.build(), call the base Node method
                # directly because we definitely *must* create this
                # directory.  The dirnode.build() method will suppress
                # the build if it's the default builder.
                SCons.Node.Node.build(dirnode)
                dirnode.get_executor().nullify()
                # The build() action may or may not have actually
                # created the directory, depending on whether the -n
                # option was used or not.  Delete the _exists and
                # _rexists attributes so they can be reevaluated.
                dirnode.clear()
            except OSError:
                pass

    def multiple_side_effect_has_builder(self):
        global MkdirBuilder
        return self.builder is not MkdirBuilder and self.has_builder()

    def alter_targets(self):
        """Return any corresponding targets in a variant directory.
        """
        return self.fs.variant_dir_target_climb(self, self, [])

    def scanner_key(self):
        """A directory does not get scanned."""
        return None

    def get_text_contents(self):
        """We already emit things in text, so just return the binary
        version."""
        return self.get_contents()

    def get_contents(self):
        """Return content signatures and names of all our children
        separated by new-lines. Ensure that the nodes are sorted."""
        return SCons.Node._get_contents_map[self._func_get_contents](self)

    def get_csig(self):
        """Compute the content signature for Directory nodes. In
        general, this is not needed and the content signature is not
        stored in the DirNodeInfo. However, if get_contents on a Dir
        node is called which has a child directory, the child
        directory should return the hash of its contents."""
        contents = self.get_contents()
        return SCons.Util.MD5signature(contents)

    def do_duplicate(self, src):
        pass

    def is_up_to_date(self):
        """If any child is not up-to-date, then this directory isn't,
        either."""
        if self.builder is not MkdirBuilder and not self.exists():
            return 0
        up_to_date = SCons.Node.up_to_date
        for kid in self.children():
            if kid.get_state() > up_to_date:
                return 0
        return 1

    def rdir(self):
        if not self.exists():
            norm_name = _my_normcase(self.name)
            for dir in self.dir.get_all_rdirs():
                try: node = dir.entries[norm_name]
                except KeyError: node = dir.dir_on_disk(self.name)
                if node and node.exists() and \
                    (isinstance(dir, Dir) or isinstance(dir, Entry)):
                        return node
        return self

    def sconsign(self):
        """Return the .sconsign file info for this directory. """
        return _sconsign_map[self._func_sconsign](self)

    def srcnode(self):
        """Dir has a special need for srcnode()...if we
        have a srcdir attribute set, then that *is* our srcnode."""
        if self.srcdir:
            return self.srcdir
        return Base.srcnode(self)

    def get_timestamp(self):
        """Return the latest timestamp from among our children"""
        stamp = 0
        for kid in self.children():
            if kid.get_timestamp() > stamp:
                stamp = kid.get_timestamp()
        return stamp

    def get_abspath(self):
        """Get the absolute path of the file."""
        return self._abspath

    def get_labspath(self):
        """Get the absolute path of the file."""
        return self._labspath

    def get_internal_path(self):
        return self._path

    def get_tpath(self):
        return self._tpath

    def get_path_elements(self):
        return self._path_elements

    def entry_abspath(self, name):
        return self._abspath + OS_SEP + name

    def entry_labspath(self, name):
        return self._labspath + '/' + name

    def entry_path(self, name):
        return self._path + OS_SEP + name

    def entry_tpath(self, name):
        return self._tpath + OS_SEP + name

    def entry_exists_on_disk(self, name):
        """ Searches through the file/dir entries of the current
            directory, and returns True if a physical entry with the given
            name could be found.

            @see rentry_exists_on_disk
        """
        try:
            d = self.on_disk_entries
        except AttributeError:
            d = {}
            try:
                entries = os.listdir(self._abspath)
            except OSError:
                pass
            else:
                for entry in map(_my_normcase, entries):
                    d[entry] = True
            self.on_disk_entries = d
        if sys.platform == 'win32' or sys.platform == 'cygwin':
            name = _my_normcase(name)
            result = d.get(name)
            if result is None:
                # Belt-and-suspenders for Windows:  check directly for
                # 8.3 file names that don't show up in os.listdir().
                result = os.path.exists(self._abspath + OS_SEP + name)
                d[name] = result
            return result
        else:
            return name in d

    def rentry_exists_on_disk(self, name):
        """ Searches through the file/dir entries of the current
            *and* all its remote directories (repos), and returns
            True if a physical entry with the given name could be found.
            The local directory (self) gets searched first, so
            repositories take a lower precedence regarding the
            searching order.

            @see entry_exists_on_disk
        """

        rentry_exists = self.entry_exists_on_disk(name)
        if not rentry_exists:
            # Search through the repository folders
            norm_name = _my_normcase(name)
            for rdir in self.get_all_rdirs():
                try:
                    node = rdir.entries[norm_name]
                    if node:
                        rentry_exists = True
                        break
                except KeyError:
                    if rdir.entry_exists_on_disk(name):
                        rentry_exists = True
                        break
        return rentry_exists

    @SCons.Memoize.CountMethodCall
    def srcdir_list(self):
        try:
            return self._memo['srcdir_list']
        except KeyError:
            pass

        result = []

        dirname = '.'
        dir = self
        while dir:
            if dir.srcdir:
                result.append(dir.srcdir.Dir(dirname))
            dirname = dir.name + OS_SEP + dirname
            dir = dir.up()

        self._memo['srcdir_list'] = result

        return result

    def srcdir_duplicate(self, name):
        for dir in self.srcdir_list():
            if self.is_under(dir):
                # We shouldn't source from something in the build path;
                # variant_dir is probably under src_dir, in which case
                # we are reflecting.
                break
            if dir.entry_exists_on_disk(name):
                srcnode = dir.Entry(name).disambiguate()
                if self.duplicate:
                    node = self.Entry(name).disambiguate()
                    node.do_duplicate(srcnode)
                    return node
                else:
                    return srcnode
        return None

    def _srcdir_find_file_key(self, filename):
        return filename

    @SCons.Memoize.CountDictCall(_srcdir_find_file_key)
    def srcdir_find_file(self, filename):
        try:
            memo_dict = self._memo['srcdir_find_file']
        except KeyError:
            memo_dict = {}
            self._memo['srcdir_find_file'] = memo_dict
        else:
            try:
                return memo_dict[filename]
            except KeyError:
                pass

        def func(node):
            if (isinstance(node, File) or isinstance(node, Entry)) and \
               (node.is_derived() or node.exists()):
                    return node
            return None

        norm_name = _my_normcase(filename)

        for rdir in self.get_all_rdirs():
            try: node = rdir.entries[norm_name]
            except KeyError: node = rdir.file_on_disk(filename)
            else: node = func(node)
            if node:
                result = (node, self)
                memo_dict[filename] = result
                return result

        for srcdir in self.srcdir_list():
            for rdir in srcdir.get_all_rdirs():
                try: node = rdir.entries[norm_name]
                except KeyError: node = rdir.file_on_disk(filename)
                else: node = func(node)
                if node:
                    result = (File(filename, self, self.fs), srcdir)
                    memo_dict[filename] = result
                    return result

        result = (None, None)
        memo_dict[filename] = result
        return result

    def dir_on_disk(self, name):
        if self.entry_exists_on_disk(name):
            try: return self.Dir(name)
            except TypeError: pass
        node = self.srcdir_duplicate(name)
        if isinstance(node, File):
            return None
        return node

    def file_on_disk(self, name):
        if self.entry_exists_on_disk(name):
            try: return self.File(name)
            except TypeError: pass
        node = self.srcdir_duplicate(name)
        if isinstance(node, Dir):
            return None
        return node

    def walk(self, func, arg):
        """
        Walk this directory tree by calling the specified function
        for each directory in the tree.

        This behaves like the os.path.walk() function, but for in-memory
        Node.FS.Dir objects.  The function takes the same arguments as
        the functions passed to os.path.walk():

                func(arg, dirname, fnames)

        Except that "dirname" will actually be the directory *Node*,
        not the string.  The '.' and '..' entries are excluded from
        fnames.  The fnames list may be modified in-place to filter the
        subdirectories visited or otherwise impose a specific order.
        The "arg" argument is always passed to func() and may be used
        in any way (or ignored, passing None is common).
        """
        entries = self.entries
        names = list(entries.keys())
        names.remove('.')
        names.remove('..')
        func(arg, self, names)
        for dirname in [n for n in names if isinstance(entries[n], Dir)]:
            entries[dirname].walk(func, arg)

    def glob(self, pathname, ondisk=True, source=False, strings=False, exclude=None):
        """
        Returns a list of Nodes (or strings) matching a specified
        pathname pattern.

        Pathname patterns follow UNIX shell semantics:  * matches
        any-length strings of any characters, ? matches any character,
        and [] can enclose lists or ranges of characters.  Matches do
        not span directory separators.

        The matches take into account Repositories, returning local
        Nodes if a corresponding entry exists in a Repository (either
        an in-memory Node or something on disk).

        By defafult, the glob() function matches entries that exist
        on-disk, in addition to in-memory Nodes.  Setting the "ondisk"
        argument to False (or some other non-true value) causes the glob()
        function to only match in-memory Nodes.  The default behavior is
        to return both the on-disk and in-memory Nodes.

        The "source" argument, when true, specifies that corresponding
        source Nodes must be returned if you're globbing in a build
        directory (initialized with VariantDir()).  The default behavior
        is to return Nodes local to the VariantDir().

        The "strings" argument, when true, returns the matches as strings,
        not Nodes.  The strings are path names relative to this directory.

        The "exclude" argument, if not None, must be a pattern or a list
        of patterns following the same UNIX shell semantics.
        Elements matching a least one pattern of this list will be excluded
        from the result.

        The underlying algorithm is adapted from the glob.glob() function
        in the Python library (but heavily modified), and uses fnmatch()
        under the covers.
        """
        dirname, basename = os.path.split(pathname)
        if not dirname:
            result = self._glob1(basename, ondisk, source, strings)
        else:
            if has_glob_magic(dirname):
                list = self.glob(dirname, ondisk, source, False, exclude)
            else:
                list = [self.Dir(dirname, create=True)]
            result = []
            for dir in list:
                r = dir._glob1(basename, ondisk, source, strings)
                if strings:
                    r = [os.path.join(str(dir), x) for x in r]
                result.extend(r)
        if exclude:
            excludes = []
            excludeList = SCons.Util.flatten(exclude)
            for x in excludeList:
                r = self.glob(x, ondisk, source, strings)
                excludes.extend(r)
            result = [x for x in result if not any(fnmatch.fnmatch(str(x), str(e)) for e in SCons.Util.flatten(excludes))]
        return sorted(result, key=lambda a: str(a))

    def _glob1(self, pattern, ondisk=True, source=False, strings=False):
        """
        Globs for and returns a list of entry names matching a single
        pattern in this directory.

        This searches any repositories and source directories for
        corresponding entries and returns a Node (or string) relative
        to the current directory if an entry is found anywhere.

        TODO: handle pattern with no wildcard
        """
        search_dir_list = self.get_all_rdirs()
        for srcdir in self.srcdir_list():
            search_dir_list.extend(srcdir.get_all_rdirs())

        selfEntry = self.Entry
        names = []
        for dir in search_dir_list:
            # We use the .name attribute from the Node because the keys of
            # the dir.entries dictionary are normalized (that is, all upper
            # case) on case-insensitive systems like Windows.
            node_names = [ v.name for k, v in dir.entries.items()
                           if k not in ('.', '..') ]
            names.extend(node_names)
            if not strings:
                # Make sure the working directory (self) actually has
                # entries for all Nodes in repositories or variant dirs.
                for name in node_names: selfEntry(name)
            if ondisk:
                try:
                    disk_names = os.listdir(dir._abspath)
                except os.error:
                    continue
                names.extend(disk_names)
                if not strings:
                    # We're going to return corresponding Nodes in
                    # the local directory, so we need to make sure
                    # those Nodes exist.  We only want to create
                    # Nodes for the entries that will match the
                    # specified pattern, though, which means we
                    # need to filter the list here, even though
                    # the overall list will also be filtered later,
                    # after we exit this loop.
                    if pattern[0] != '.':
                        disk_names = [x for x in disk_names if x[0] != '.']
                    disk_names = fnmatch.filter(disk_names, pattern)
                    dirEntry = dir.Entry
                    for name in disk_names:
                        # Add './' before disk filename so that '#' at
                        # beginning of filename isn't interpreted.
                        name = './' + name
                        node = dirEntry(name).disambiguate()
                        n = selfEntry(name)
                        if n.__class__ != node.__class__:
                            n.__class__ = node.__class__
                            n._morph()

        names = set(names)
        if pattern[0] != '.':
            names = [x for x in names if x[0] != '.']
        names = fnmatch.filter(names, pattern)

        if strings:
            return names

        return [self.entries[_my_normcase(n)] for n in names]

class RootDir(Dir):
    """A class for the root directory of a file system.

    This is the same as a Dir class, except that the path separator
    ('/' or '\\') is actually part of the name, so we don't need to
    add a separator when creating the path names of entries within
    this directory.
    """

    __slots__ = ('_lookupDict', )

    def __init__(self, drive, fs):
        if SCons.Debug.track_instances: logInstanceCreation(self, 'Node.FS.RootDir')
        SCons.Node.Node.__init__(self)

        # Handle all the types of drives:
        if drive == '':
            # No drive, regular UNIX root or Windows default drive.
            name = OS_SEP
            dirname = OS_SEP
        elif drive == '//':
            # UNC path
            name = UNC_PREFIX
            dirname = UNC_PREFIX
        else:
            # Windows drive letter
            name = drive
            dirname = drive + OS_SEP

        # Filename with extension as it was specified when the object was
        # created; to obtain filesystem path, use Python str() function
        self.name = SCons.Util.silent_intern(name)
        self.fs = fs #: Reference to parent Node.FS object

        self._path_elements = [self]
        self.dir = self
        self._func_rexists = 2
        self._func_target_from_source = 1
        self.store_info = 1

        # Now set our paths to what we really want them to be. The
        # name should already contain any necessary separators, such
        # as the initial drive letter (the name) plus the directory
        # separator, except for the "lookup abspath," which does not
        # have the drive letter.
        self._abspath = dirname
        self._labspath = ''
        self._path = dirname
        self._tpath = dirname
        self.dirname = dirname

        self._morph()

        self.duplicate = 0
        self._lookupDict = {}

        self._lookupDict[''] = self
        self._lookupDict['/'] = self
        self.root = self
        # The // entry is necessary because os.path.normpath()
        # preserves double slashes at the beginning of a path on Posix
        # platforms.
        if not has_unc:
            self._lookupDict['//'] = self

    def _morph(self):
        """Turn a file system Node (either a freshly initialized directory
        object or a separate Entry object) into a proper directory object.

        Set up this directory's entries and hook it into the file
        system tree.  Specify that directories (this Node) don't use
        signatures for calculating whether they're current.
        """

        self.repositories = []
        self.srcdir = None

        self.entries = {}
        self.entries['.'] = self
        self.entries['..'] = self.dir
        self.cwd = self
        self.searched = 0
        self._sconsign = None
        self.variant_dirs = []
        self.changed_since_last_build = 3
        self._func_sconsign = 1
        self._func_exists = 2
        self._func_get_contents = 2

        # Don't just reset the executor, replace its action list,
        # because it might have some pre-or post-actions that need to
        # be preserved.
        #
        # But don't reset the executor if there is a non-null executor
        # attached already. The existing executor might have other
        # targets, in which case replacing the action list with a
        # Mkdir action is a big mistake.
        if not hasattr(self, 'executor'):
            self.builder = get_MkdirBuilder()
            self.get_executor().set_action_list(self.builder.action)
        else:
            # Prepend MkdirBuilder action to existing action list
            l = self.get_executor().action_list
            a = get_MkdirBuilder().action
            l.insert(0, a)
            self.get_executor().set_action_list(l)


    def must_be_same(self, klass):
        if klass is Dir:
            return
        Base.must_be_same(self, klass)

    def _lookup_abs(self, p, klass, create=1):
        """
        Fast (?) lookup of a *normalized* absolute path.

        This method is intended for use by internal lookups with
        already-normalized path data.  For general-purpose lookups,
        use the FS.Entry(), FS.Dir() or FS.File() methods.

        The caller is responsible for making sure we're passed a
        normalized absolute path; we merely let Python's dictionary look
        up and return the One True Node.FS object for the path.

        If a Node for the specified "p" doesn't already exist, and
        "create" is specified, the Node may be created after recursive
        invocation to find or create the parent directory or directories.
        """
        k = _my_normcase(p)
        try:
            result = self._lookupDict[k]
        except KeyError:
            if not create:
                msg = "No such file or directory: '%s' in '%s' (and create is False)" % (p, str(self))
                raise SCons.Errors.UserError(msg)
            # There is no Node for this path name, and we're allowed
            # to create it.
            dir_name, file_name = p.rsplit('/',1)
            dir_node = self._lookup_abs(dir_name, Dir)
            result = klass(file_name, dir_node, self.fs)

            # Double-check on disk (as configured) that the Node we
            # created matches whatever is out there in the real world.
            result.diskcheck_match()

            self._lookupDict[k] = result
            dir_node.entries[_my_normcase(file_name)] = result
            dir_node.implicit = None
        else:
            # There is already a Node for this path name.  Allow it to
            # complain if we were looking for an inappropriate type.
            result.must_be_same(klass)
        return result

    def __str__(self):
        return self._abspath

    def entry_abspath(self, name):
        return self._abspath + name

    def entry_labspath(self, name):
        return '/' + name

    def entry_path(self, name):
        return self._path + name

    def entry_tpath(self, name):
        return self._tpath + name

    def is_under(self, dir):
        if self is dir:
            return 1
        else:
            return 0

    def up(self):
        return None

    def get_dir(self):
        return None

    def src_builder(self):
        return _null


class FileNodeInfo(SCons.Node.NodeInfoBase):
    __slots__ = ('csig', 'timestamp', 'size')
    current_version_id = 2

    field_list = ['csig', 'timestamp', 'size']

    # This should get reset by the FS initialization.
    fs = None

    def str_to_node(self, s):
        top = self.fs.Top
        root = top.root
        if do_splitdrive:
            drive, s = _my_splitdrive(s)
            if drive:
                root = self.fs.get_root(drive)
        if not os.path.isabs(s):
            s = top.get_labspath() + '/' + s
        return root._lookup_abs(s, Entry)

    def __getstate__(self):
        """
        Return all fields that shall be pickled. Walk the slots in the class
        hierarchy and add those to the state dictionary. If a '__dict__' slot is
        available, copy all entries to the dictionary. Also include the version
        id, which is fixed for all instances of a class.
        """
        state = getattr(self, '__dict__', {}).copy()
        for obj in type(self).mro():
            for name in getattr(obj, '__slots__', ()):
                if hasattr(self, name):
                    state[name] = getattr(self, name)

        state['_version_id'] = self.current_version_id
        try:
            del state['__weakref__']
        except KeyError:
            pass

        return state

    def __setstate__(self, state):
        """
        Restore the attributes from a pickled state.
        """
        # TODO check or discard version
        del state['_version_id']
        for key, value in state.items():
            if key not in ('__weakref__',):
                setattr(self, key, value)

    def __eq__(self, other):
        return self.csig == other.csig and self.timestamp == other.timestamp and self.size == other.size

    def __ne__(self, other):
        return not self.__eq__(other)


class FileBuildInfo(SCons.Node.BuildInfoBase):
    """
    This is info loaded from sconsign.

    Attributes unique to FileBuildInfo:
        dependency_map : Caches file->csig mapping
                    for all dependencies.  Currently this is only used when using
                    MD5-timestamp decider.
                    It's used to ensure that we copy the correct
                    csig from previous build to be written to .sconsign when current build
                    is done. Previously the matching of csig to file was strictly by order
                    they appeared in bdepends, bsources, or bimplicit, and so a change in order
                    or count of any of these could yield writing wrong csig, and then false positive
                    rebuilds
    """
    __slots__ = ['dependency_map', ]
    current_version_id = 2

    def __setattr__(self, key, value):

        # If any attributes are changed in FileBuildInfo, we need to
        # invalidate the cached map of file name to content signature
        # heald in dependency_map. Currently only used with
        # MD5-timestamp decider
        if key != 'dependency_map' and hasattr(self, 'dependency_map'):
            del self.dependency_map

        return super(FileBuildInfo, self).__setattr__(key, value)

    def convert_to_sconsign(self):
        """
        Converts this FileBuildInfo object for writing to a .sconsign file

        This replaces each Node in our various dependency lists with its
        usual string representation: relative to the top-level SConstruct
        directory, or an absolute path if it's outside.
        """
        if os_sep_is_slash:
            node_to_str = str
        else:
            def node_to_str(n):
                try:
                    s = n.get_internal_path()
                except AttributeError:
                    s = str(n)
                else:
                    s = s.replace(OS_SEP, '/')
                return s
        for attr in ['bsources', 'bdepends', 'bimplicit']:
            try:
                val = getattr(self, attr)
            except AttributeError:
                pass
            else:
                setattr(self, attr, list(map(node_to_str, val)))

    def convert_from_sconsign(self, dir, name):
        """
        Converts a newly-read FileBuildInfo object for in-SCons use

        For normal up-to-date checking, we don't have any conversion to
        perform--but we're leaving this method here to make that clear.
        """
        pass

    def prepare_dependencies(self):
        """
        Prepares a FileBuildInfo object for explaining what changed

        The bsources, bdepends and bimplicit lists have all been
        stored on disk as paths relative to the top-level SConstruct
        directory.  Convert the strings to actual Nodes (for use by the
        --debug=explain code and --implicit-cache).
        """
        attrs = [
            ('bsources', 'bsourcesigs'),
            ('bdepends', 'bdependsigs'),
            ('bimplicit', 'bimplicitsigs'),
        ]
        for (nattr, sattr) in attrs:
            try:
                strings = getattr(self, nattr)
                nodeinfos = getattr(self, sattr)
            except AttributeError:
                continue
            if strings is None or nodeinfos is None:
                continue
            nodes = []
            for s, ni in zip(strings, nodeinfos):
                if not isinstance(s, SCons.Node.Node):
                    s = ni.str_to_node(s)
                nodes.append(s)
            setattr(self, nattr, nodes)

    def format(self, names=0):
        result = []
        bkids = self.bsources + self.bdepends + self.bimplicit
        bkidsigs = self.bsourcesigs + self.bdependsigs + self.bimplicitsigs
        for bkid, bkidsig in zip(bkids, bkidsigs):
            result.append(str(bkid) + ': ' +
                          ' '.join(bkidsig.format(names=names)))
        if not hasattr(self,'bact'):
            self.bact = "none"
        result.append('%s [%s]' % (self.bactsig, self.bact))
        return '\n'.join(result)


class File(Base):
    """A class for files in a file system.
    """

    __slots__ = ['scanner_paths',
                 'cachedir_csig',
                 'cachesig',
                 'repositories',
                 'srcdir',
                 'entries',
                 'searched',
                 '_sconsign',
                 'variant_dirs',
                 'root',
                 'dirname',
                 'on_disk_entries',
                 'released_target_info',
                 'contentsig']

    NodeInfo = FileNodeInfo
    BuildInfo = FileBuildInfo

    md5_chunksize = 64

    def diskcheck_match(self):
        diskcheck_match(self, self.isdir,
                        "Directory %s found where file expected.")

    def __init__(self, name, directory, fs):
        if SCons.Debug.track_instances: logInstanceCreation(self, 'Node.FS.File')
        Base.__init__(self, name, directory, fs)
        self._morph()

    def Entry(self, name):
        """Create an entry node named 'name' relative to
        the directory of this file."""
        return self.dir.Entry(name)

    def Dir(self, name, create=True):
        """Create a directory node named 'name' relative to
        the directory of this file."""
        return self.dir.Dir(name, create=create)

    def Dirs(self, pathlist):
        """Create a list of directories relative to the SConscript
        directory of this file."""
        return [self.Dir(p) for p in pathlist]

    def File(self, name):
        """Create a file node named 'name' relative to
        the directory of this file."""
        return self.dir.File(name)

    def _morph(self):
        """Turn a file system node into a File object."""
        self.scanner_paths = {}
        if not hasattr(self, '_local'):
            self._local = 0
        if not hasattr(self, 'released_target_info'):
            self.released_target_info = False

        self.store_info = 1
        self._func_exists = 4
        self._func_get_contents = 3

        # Initialize this Node's decider function to decide_source() because
        # every file is a source file until it has a Builder attached...
        self.changed_since_last_build = 4

        # If there was already a Builder set on this entry, then
        # we need to make sure we call the target-decider function,
        # not the source-decider.  Reaching in and doing this by hand
        # is a little bogus.  We'd prefer to handle this by adding
        # an Entry.builder_set() method that disambiguates like the
        # other methods, but that starts running into problems with the
        # fragile way we initialize Dir Nodes with their Mkdir builders,
        # yet still allow them to be overridden by the user.  Since it's
        # not clear right now how to fix that, stick with what works
        # until it becomes clear...
        if self.has_builder():
            self.changed_since_last_build = 5

    def scanner_key(self):
        return self.get_suffix()

    def get_contents(self):
        return SCons.Node._get_contents_map[self._func_get_contents](self)

    def get_text_contents(self):
        """
        This attempts to figure out what the encoding of the text is
        based upon the BOM bytes, and then decodes the contents so that
        it's a valid python string.
        """
        contents = self.get_contents()
        # The behavior of various decode() methods and functions
        # w.r.t. the initial BOM bytes is different for different
        # encodings and/or Python versions.  ('utf-8' does not strip
        # them, but has a 'utf-8-sig' which does; 'utf-16' seems to
        # strip them; etc.)  Just sidestep all the complication by
        # explicitly stripping the BOM before we decode().
        if contents[:len(codecs.BOM_UTF8)] == codecs.BOM_UTF8:
            return contents[len(codecs.BOM_UTF8):].decode('utf-8')
        if contents[:len(codecs.BOM_UTF16_LE)] == codecs.BOM_UTF16_LE:
            return contents[len(codecs.BOM_UTF16_LE):].decode('utf-16-le')
        if contents[:len(codecs.BOM_UTF16_BE)] == codecs.BOM_UTF16_BE:
            return contents[len(codecs.BOM_UTF16_BE):].decode('utf-16-be')
        try:
            return contents.decode('utf-8')
        except UnicodeDecodeError as e:
            try:
                return contents.decode('latin-1')
            except UnicodeDecodeError as e:
                return contents.decode('utf-8', error='backslashreplace')


    def get_content_hash(self):
        """
        Compute and return the MD5 hash for this file.
        """
        if not self.rexists():
            return SCons.Util.MD5signature('')
        fname = self.rfile().get_abspath()
        try:
            cs = SCons.Util.MD5filesignature(fname,
                chunksize=SCons.Node.FS.File.md5_chunksize*1024)
        except EnvironmentError as e:
            if not e.filename:
                e.filename = fname
            raise
        return cs

    @SCons.Memoize.CountMethodCall
    def get_size(self):
        try:
            return self._memo['get_size']
        except KeyError:
            pass

        if self.rexists():
            size = self.rfile().getsize()
        else:
            size = 0

        self._memo['get_size'] = size

        return size

    @SCons.Memoize.CountMethodCall
    def get_timestamp(self):
        try:
            return self._memo['get_timestamp']
        except KeyError:
            pass

        if self.rexists():
            timestamp = self.rfile().getmtime()
        else:
            timestamp = 0

        self._memo['get_timestamp'] = timestamp

        return timestamp

    convert_copy_attrs = [
        'bsources',
        'bimplicit',
        'bdepends',
        'bact',
        'bactsig',
        'ninfo',
    ]


    convert_sig_attrs = [
        'bsourcesigs',
        'bimplicitsigs',
        'bdependsigs',
    ]

    def convert_old_entry(self, old_entry):
        # Convert a .sconsign entry from before the Big Signature
        # Refactoring, doing what we can to convert its information
        # to the new .sconsign entry format.
        #
        # The old format looked essentially like this:
        #
        #   BuildInfo
        #       .ninfo (NodeInfo)
        #           .bsig
        #           .csig
        #           .timestamp
        #           .size
        #       .bsources
        #       .bsourcesigs ("signature" list)
        #       .bdepends
        #       .bdependsigs ("signature" list)
        #       .bimplicit
        #       .bimplicitsigs ("signature" list)
        #       .bact
        #       .bactsig
        #
        # The new format looks like this:
        #
        #   .ninfo (NodeInfo)
        #       .bsig
        #       .csig
        #       .timestamp
        #       .size
        #   .binfo (BuildInfo)
        #       .bsources
        #       .bsourcesigs (NodeInfo list)
        #           .bsig
        #           .csig
        #           .timestamp
        #           .size
        #       .bdepends
        #       .bdependsigs (NodeInfo list)
        #           .bsig
        #           .csig
        #           .timestamp
        #           .size
        #       .bimplicit
        #       .bimplicitsigs (NodeInfo list)
        #           .bsig
        #           .csig
        #           .timestamp
        #           .size
        #       .bact
        #       .bactsig
        #
        # The basic idea of the new structure is that a NodeInfo always
        # holds all available information about the state of a given Node
        # at a certain point in time.  The various .b*sigs lists can just
        # be a list of pointers to the .ninfo attributes of the different
        # dependent nodes, without any copying of information until it's
        # time to pickle it for writing out to a .sconsign file.
        #
        # The complicating issue is that the *old* format only stored one
        # "signature" per dependency, based on however the *last* build
        # was configured.  We don't know from just looking at it whether
        # it was a build signature, a content signature, or a timestamp
        # "signature".  Since we no longer use build signatures, the
        # best we can do is look at the length and if it's thirty two,
        # assume that it was (or might have been) a content signature.
        # If it was actually a build signature, then it will cause a
        # rebuild anyway when it doesn't match the new content signature,
        # but that's probably the best we can do.
        import SCons.SConsign
        new_entry = SCons.SConsign.SConsignEntry()
        new_entry.binfo = self.new_binfo()
        binfo = new_entry.binfo
        for attr in self.convert_copy_attrs:
            try:
                value = getattr(old_entry, attr)
            except AttributeError:
                continue
            setattr(binfo, attr, value)
            delattr(old_entry, attr)
        for attr in self.convert_sig_attrs:
            try:
                sig_list = getattr(old_entry, attr)
            except AttributeError:
                continue
            value = []
            for sig in sig_list:
                ninfo = self.new_ninfo()
                if len(sig) == 32:
                    ninfo.csig = sig
                else:
                    ninfo.timestamp = sig
                value.append(ninfo)
            setattr(binfo, attr, value)
            delattr(old_entry, attr)
        return new_entry

    @SCons.Memoize.CountMethodCall
    def get_stored_info(self):
        try:
            return self._memo['get_stored_info']
        except KeyError:
            pass

        try:
            sconsign_entry = self.dir.sconsign().get_entry(self.name)
        except (KeyError, EnvironmentError):
            import SCons.SConsign
            sconsign_entry = SCons.SConsign.SConsignEntry()
            sconsign_entry.binfo = self.new_binfo()
            sconsign_entry.ninfo = self.new_ninfo()
        else:
            if isinstance(sconsign_entry, FileBuildInfo):
                # This is a .sconsign file from before the Big Signature
                # Refactoring; convert it as best we can.
                sconsign_entry = self.convert_old_entry(sconsign_entry)
            try:
                delattr(sconsign_entry.ninfo, 'bsig')
            except AttributeError:
                pass

        self._memo['get_stored_info'] = sconsign_entry

        return sconsign_entry

    def get_stored_implicit(self):
        binfo = self.get_stored_info().binfo
        binfo.prepare_dependencies()
        try: return binfo.bimplicit
        except AttributeError: return None

    def rel_path(self, other):
        return self.dir.rel_path(other)

    def _get_found_includes_key(self, env, scanner, path):
        return (id(env), id(scanner), path)

    @SCons.Memoize.CountDictCall(_get_found_includes_key)
    def get_found_includes(self, env, scanner, path):
        """Return the included implicit dependencies in this file.
        Cache results so we only scan the file once per path
        regardless of how many times this information is requested.
        """
        memo_key = (id(env), id(scanner), path)
        try:
            memo_dict = self._memo['get_found_includes']
        except KeyError:
            memo_dict = {}
            self._memo['get_found_includes'] = memo_dict
        else:
            try:
                return memo_dict[memo_key]
            except KeyError:
                pass

        if scanner:
            result = [n.disambiguate() for n in scanner(self, env, path)]
        else:
            result = []

        memo_dict[memo_key] = result

        return result

    def _createDir(self):
        # ensure that the directories for this node are
        # created.
        self.dir._create()

    def push_to_cache(self):
        """Try to push the node into a cache
        """
        # This should get called before the Nodes' .built() method is
        # called, which would clear the build signature if the file has
        # a source scanner.
        #
        # We have to clear the local memoized values *before* we push
        # the node to cache so that the memoization of the self.exists()
        # return value doesn't interfere.
        if self.nocache:
            return
        self.clear_memoized_values()
        if self.exists():
            self.get_build_env().get_CacheDir().push(self)

    def retrieve_from_cache(self):
        """Try to retrieve the node's content from a cache

        This method is called from multiple threads in a parallel build,
        so only do thread safe stuff here. Do thread unsafe stuff in
        built().

        Returns true if the node was successfully retrieved.
        """
        if self.nocache:
            return None
        if not self.is_derived():
            return None
        return self.get_build_env().get_CacheDir().retrieve(self)

    def visited(self):
        if self.exists() and self.executor is not None:
            self.get_build_env().get_CacheDir().push_if_forced(self)

        ninfo = self.get_ninfo()

        csig = self.get_max_drift_csig()
        if csig:
            ninfo.csig = csig

        ninfo.timestamp = self.get_timestamp()
        ninfo.size      = self.get_size()

        if not self.has_builder():
            # This is a source file, but it might have been a target file
            # in another build that included more of the DAG.  Copy
            # any build information that's stored in the .sconsign file
            # into our binfo object so it doesn't get lost.
            old = self.get_stored_info()
            self.get_binfo().merge(old.binfo)

        SCons.Node.store_info_map[self.store_info](self)

    def release_target_info(self):
        """Called just after this node has been marked
         up-to-date or was built completely.

         This is where we try to release as many target node infos
         as possible for clean builds and update runs, in order
         to minimize the overall memory consumption.

         We'd like to remove a lot more attributes like self.sources
         and self.sources_set, but they might get used
         in a next build step. For example, during configuration
         the source files for a built E{*}.o file are used to figure out
         which linker to use for the resulting Program (gcc vs. g++)!
         That's why we check for the 'keep_targetinfo' attribute,
         config Nodes and the Interactive mode just don't allow
         an early release of most variables.

         In the same manner, we can't simply remove the self.attributes
         here. The smart linking relies on the shared flag, and some
         parts of the java Tool use it to transport information
         about nodes...

         @see: built() and Node.release_target_info()
         """
        if (self.released_target_info or SCons.Node.interactive):
            return

        if not hasattr(self.attributes, 'keep_targetinfo'):
            # Cache some required values, before releasing
            # stuff like env, executor and builder...
            self.changed(allowcache=True)
            self.get_contents_sig()
            self.get_build_env()
            # Now purge unneeded stuff to free memory...
            self.executor = None
            self._memo.pop('rfile', None)
            self.prerequisites = None
            # Cleanup lists, but only if they're empty
            if not len(self.ignore_set):
                self.ignore_set = None
            if not len(self.implicit_set):
                self.implicit_set = None
            if not len(self.depends_set):
                self.depends_set = None
            if not len(self.ignore):
                self.ignore = None
            if not len(self.depends):
                self.depends = None
            # Mark this node as done, we only have to release
            # the memory once...
            self.released_target_info = True

    def find_src_builder(self):
        if self.rexists():
            return None
        scb = self.dir.src_builder()
        if scb is _null:
            scb = None
        if scb is not None:
            try:
                b = self.builder
            except AttributeError:
                b = None
            if b is None:
                self.builder_set(scb)
        return scb

    def has_src_builder(self):
        """Return whether this Node has a source builder or not.

        If this Node doesn't have an explicit source code builder, this
        is where we figure out, on the fly, if there's a transparent
        source code builder for it.

        Note that if we found a source builder, we also set the
        self.builder attribute, so that all of the methods that actually
        *build* this file don't have to do anything different.
        """
        try:
            scb = self.sbuilder
        except AttributeError:
            scb = self.sbuilder = self.find_src_builder()
        return scb is not None

    def alter_targets(self):
        """Return any corresponding targets in a variant directory.
        """
        if self.is_derived():
            return [], None
        return self.fs.variant_dir_target_climb(self, self.dir, [self.name])

    def _rmv_existing(self):
        self.clear_memoized_values()
        if SCons.Node.print_duplicate:
            print("dup: removing existing target {}".format(self))
        e = Unlink(self, [], None)
        if isinstance(e, SCons.Errors.BuildError):
            raise e

    #
    # Taskmaster interface subsystem
    #

    def make_ready(self):
        self.has_src_builder()
        self.get_binfo()

    def prepare(self):
        """Prepare for this file to be created."""
        SCons.Node.Node.prepare(self)

        if self.get_state() != SCons.Node.up_to_date:
            if self.exists():
                if self.is_derived() and not self.precious:
                    self._rmv_existing()
            else:
                try:
                    self._createDir()
                except SCons.Errors.StopError as drive:
                    raise SCons.Errors.StopError("No drive `{}' for target `{}'.".format(drive, self))

    #
    #
    #

    def remove(self):
        """Remove this file."""
        if self.exists() or self.islink():
            self.fs.unlink(self.get_internal_path())
            return 1
        return None

    def do_duplicate(self, src):
        self._createDir()
        if SCons.Node.print_duplicate:
            print("dup: relinking variant '{}' from '{}'".format(self, src))
        Unlink(self, None, None)
        e = Link(self, src, None)
        if isinstance(e, SCons.Errors.BuildError):
            raise SCons.Errors.StopError("Cannot duplicate `{}' in `{}': {}.".format(src.get_internal_path(), self.dir._path, e.errstr))
        self.linked = 1
        # The Link() action may or may not have actually
        # created the file, depending on whether the -n
        # option was used or not.  Delete the _exists and
        # _rexists attributes so they can be reevaluated.
        self.clear()

    @SCons.Memoize.CountMethodCall
    def exists(self):
        try:
            return self._memo['exists']
        except KeyError:
            pass
        result = SCons.Node._exists_map[self._func_exists](self)
        self._memo['exists'] = result
        return result

    #
    # SIGNATURE SUBSYSTEM
    #

    def get_max_drift_csig(self):
        """
        Returns the content signature currently stored for this node
        if it's been unmodified longer than the max_drift value, or the
        max_drift value is 0.  Returns None otherwise.
        """
        old = self.get_stored_info()
        mtime = self.get_timestamp()

        max_drift = self.fs.max_drift
        if max_drift > 0:
            if (time.time() - mtime) > max_drift:
                try:
                    n = old.ninfo
                    if n.timestamp and n.csig and n.timestamp == mtime:
                        return n.csig
                except AttributeError:
                    pass
        elif max_drift == 0:
            try:
                return old.ninfo.csig
            except AttributeError:
                pass

        return None

    def get_csig(self):
        """
        Generate a node's content signature, the digested signature
        of its content.

        node - the node
        cache - alternate node to use for the signature cache
        returns - the content signature
        """
        ninfo = self.get_ninfo()
        try:
            return ninfo.csig
        except AttributeError:
            pass

        csig = self.get_max_drift_csig()
        if csig is None:

            try:
                if self.get_size() < SCons.Node.FS.File.md5_chunksize:
                    contents = self.get_contents()
                else:
                    csig = self.get_content_hash()
            except IOError:
                # This can happen if there's actually a directory on-disk,
                # which can be the case if they've disabled disk checks,
                # or if an action with a File target actually happens to
                # create a same-named directory by mistake.
                csig = ''
            else:
                if not csig:
                    csig = SCons.Util.MD5signature(contents)

        ninfo.csig = csig

        return csig

    #
    # DECISION SUBSYSTEM
    #

    def builder_set(self, builder):
        SCons.Node.Node.builder_set(self, builder)
        self.changed_since_last_build = 5

    def built(self):
        """Called just after this File node is successfully built.

         Just like for 'release_target_info' we try to release
         some more target node attributes in order to minimize the
         overall memory consumption.

         @see: release_target_info
        """

        SCons.Node.Node.built(self)

        if (not SCons.Node.interactive and
            not hasattr(self.attributes, 'keep_targetinfo')):
            # Ensure that the build infos get computed and cached...
            SCons.Node.store_info_map[self.store_info](self)
            # ... then release some more variables.
            self._specific_sources = False
            self._labspath = None
            self._save_str()
            self.cwd = None

            self.scanner_paths = None

    def changed(self, node=None, allowcache=False):
        """
        Returns if the node is up-to-date with respect to the BuildInfo
        stored last time it was built.

        For File nodes this is basically a wrapper around Node.changed(),
        but we allow the return value to get cached after the reference
        to the Executor got released in release_target_info().

        @see: Node.changed()
        """
        if node is None:
            try:
                return self._memo['changed']
            except KeyError:
                pass

        has_changed = SCons.Node.Node.changed(self, node)
        if allowcache:
            self._memo['changed'] = has_changed
        return has_changed

    def changed_content(self, target, prev_ni, repo_node=None):
        cur_csig = self.get_csig()
        try:
            return cur_csig != prev_ni.csig
        except AttributeError:
            return 1

    def changed_state(self, target, prev_ni, repo_node=None):
        return self.state != SCons.Node.up_to_date


    # Caching node -> string mapping for the below method
    __dmap_cache = {}
    __dmap_sig_cache = {}


    def _build_dependency_map(self, binfo):
        """
        Build mapping from file -> signature

        Args:
            self - self
            binfo - buildinfo from node being considered

        Returns:
            dictionary of file->signature mappings
        """

        # For an "empty" binfo properties like bsources
        # do not exist: check this to avoid exception.
        if (len(binfo.bsourcesigs) + len(binfo.bdependsigs) + \
            len(binfo.bimplicitsigs)) == 0:
            return {}

        binfo.dependency_map = { child:signature for child, signature in zip(chain(binfo.bsources, binfo.bdepends, binfo.bimplicit),
                                     chain(binfo.bsourcesigs, binfo.bdependsigs, binfo.bimplicitsigs))}

        return binfo.dependency_map

    # @profile
    def _add_strings_to_dependency_map(self, dmap):
        """
        In the case comparing node objects isn't sufficient, we'll add the strings for the nodes to the dependency map
        :return:
        """

        first_string = str(next(iter(dmap)))

        # print("DMAP:%s"%id(dmap))
        if first_string not in dmap:
                string_dict = {str(child): signature for child, signature in dmap.items()}
                dmap.update(string_dict)
        return dmap

    def _get_previous_signatures(self, dmap):
        """
        Return a list of corresponding csigs from previous
        build in order of the node/files in children.

        Args:
            self - self
            dmap - Dictionary of file -> csig

        Returns:
            List of csigs for provided list of children
        """
        prev = []
        # MD5_TIMESTAMP_DEBUG = False

        if len(dmap) == 0:
            if MD5_TIMESTAMP_DEBUG: print("Nothing dmap shortcutting")
            return None
        elif MD5_TIMESTAMP_DEBUG: print("len(dmap):%d"%len(dmap))


        # First try retrieving via Node
        if MD5_TIMESTAMP_DEBUG: print("Checking if self is in  map:%s id:%s type:%s"%(str(self), id(self), type(self)))
        df = dmap.get(self, False)
        if df:
            return df

        # Now check if self's repository file is in map.
        rf = self.rfile()
        if MD5_TIMESTAMP_DEBUG: print("Checking if self.rfile  is in  map:%s id:%s type:%s"%(str(rf), id(rf), type(rf)))
        rfm = dmap.get(rf, False)
        if rfm:
            return rfm

        # get default string for node and then also string swapping os.altsep for os.sep (/ for \)
        c_strs = [str(self)]

        if os.altsep:
            c_strs.append(c_strs[0].replace(os.sep, os.altsep))

        # In some cases the dependency_maps' keys are already strings check.
        # Check if either string is now in dmap.
        for s in c_strs:
            if MD5_TIMESTAMP_DEBUG: print("Checking if str(self) is in map  :%s" % s)
            df = dmap.get(s, False)
            if df:
                return df

        # Strings don't exist in map, add them and try again
        # If there are no strings in this dmap, then add them.
        # This may not be necessary, we could walk the nodes in the dmap and check each string
        # rather than adding ALL the strings to dmap. In theory that would be n/2 vs 2n str() calls on node
        # if not dmap.has_strings:
        dmap = self._add_strings_to_dependency_map(dmap)

        # In some cases the dependency_maps' keys are already strings check.
        # Check if either string is now in dmap.
        for s in c_strs:
            if MD5_TIMESTAMP_DEBUG: print("Checking if str(self) is in map (now with strings)  :%s" % s)
            df = dmap.get(s, False)
            if df:
                return df

        # Lastly use nodes get_path() to generate string and see if that's in dmap
        if not df:
            try:
                # this should yield a path which matches what's in the sconsign
                c_str = self.get_path()
                if os.altsep:
                    c_str = c_str.replace(os.sep, os.altsep)

                if MD5_TIMESTAMP_DEBUG: print("Checking if self.get_path is in map (now with strings)  :%s" % s)

                df = dmap.get(c_str, None)

            except AttributeError as e:
                raise FileBuildInfoFileToCsigMappingError("No mapping from file name to content signature for :%s"%c_str)

        return df

    def changed_timestamp_then_content(self, target, prev_ni, node=None):
        """
        Used when decider for file is Timestamp-MD5

        NOTE: If the timestamp hasn't changed this will skip md5'ing the
              file and just copy the prev_ni provided.  If the prev_ni
              is wrong. It will propagate it.
              See: https://github.com/SCons/scons/issues/2980

        Args:
            self - dependency
            target - target
            prev_ni - The NodeInfo object loaded from previous builds .sconsign
            node - Node instance.  Check this node for file existence/timestamp
                   if specified.

        Returns:
            Boolean - Indicates if node(File) has changed.
        """

        if node is None:
            node = self
        # Now get sconsign name -> csig map and then get proper prev_ni if possible
        bi = node.get_stored_info().binfo
        rebuilt = False
        try:
            dependency_map = bi.dependency_map
        except AttributeError as e:
            dependency_map = self._build_dependency_map(bi)
            rebuilt = True

        if len(dependency_map) == 0:
            # If there's no dependency map, there's no need to find the
            # prev_ni as there aren't any
            # shortcut the rest of the logic
            if MD5_TIMESTAMP_DEBUG: print("Skipping checks len(dmap)=0")

            # We still need to get the current file's csig
            # This should be slightly faster than calling self.changed_content(target, new_prev_ni)
            self.get_csig()
            return True

        new_prev_ni = self._get_previous_signatures(dependency_map)
        new = self.changed_timestamp_match(target, new_prev_ni)

        if MD5_TIMESTAMP_DEBUG:
            old = self.changed_timestamp_match(target, prev_ni)

            if old != new:
                print("Mismatch self.changed_timestamp_match(%s, prev_ni) old:%s new:%s"%(str(target), old, new))
                new_prev_ni = self._get_previous_signatures(dependency_map)

        if not new:
            try:
                # NOTE: We're modifying the current node's csig in a query.
                self.get_ninfo().csig = new_prev_ni.csig
            except AttributeError:
                pass
            return False
        return self.changed_content(target, new_prev_ni)

    def changed_timestamp_newer(self, target, prev_ni, repo_node=None):
        try:
            return self.get_timestamp() > target.get_timestamp()
        except AttributeError:
            return 1

    def changed_timestamp_match(self, target, prev_ni, repo_node=None):
        """
        Return True if the timestamps don't match or if there is no previous timestamp
        :param target:
        :param prev_ni: Information about the node from the previous build
        :return:
        """
        try:
            return self.get_timestamp() != prev_ni.timestamp
        except AttributeError:
            return 1

    def is_up_to_date(self):
        """Check for whether the Node is current
           In all cases self is the target we're checking to see if it's up to date
        """

        T = 0
        if T: Trace('is_up_to_date(%s):' % self)
        if not self.exists():
            if T: Trace(' not self.exists():')
            # The file (always a target) doesn't exist locally...
            r = self.rfile()
            if r != self:
                # ...but there is one (always a target) in a Repository...
                if not self.changed(r):
                    if T: Trace(' changed(%s):' % r)
                    # ...and it's even up-to-date...
                    if self._local:
                        # ...and they'd like a local copy.
                        e = LocalCopy(self, r, None)
                        if isinstance(e, SCons.Errors.BuildError):
                            # Likely this should be re-raising exception e
                            # (which would be BuildError)
                            raise e
                        SCons.Node.store_info_map[self.store_info](self)
                    if T: Trace(' 1\n')
                    return 1
            self.changed()
            if T: Trace(' None\n')
            return None
        else:
            r = self.changed()
            if T: Trace(' self.exists():  %s\n' % r)
            return not r

    @SCons.Memoize.CountMethodCall
    def rfile(self):
        try:
            return self._memo['rfile']
        except KeyError:
            pass
        result = self
        if not self.exists():
            norm_name = _my_normcase(self.name)
            for repo_dir in self.dir.get_all_rdirs():
                try:
                    node = repo_dir.entries[norm_name]
                except KeyError:
                    node = repo_dir.file_on_disk(self.name)

                if node and node.exists() and \
                   (isinstance(node, File) or isinstance(node, Entry)
                    or not node.is_derived()):
                        result = node
                        # Copy over our local attributes to the repository
                        # Node so we identify shared object files in the
                        # repository and don't assume they're static.
                        #
                        # This isn't perfect; the attribute would ideally
                        # be attached to the object in the repository in
                        # case it was built statically in the repository
                        # and we changed it to shared locally, but that's
                        # rarely the case and would only occur if you
                        # intentionally used the same suffix for both
                        # shared and static objects anyway.  So this
                        # should work well in practice.
                        result.attributes = self.attributes
                        break
        self._memo['rfile'] = result
        return result

    def find_repo_file(self):
        """
        For this node, find if there exists a corresponding file in one or more repositories
        :return: list of corresponding files in repositories
        """
        retvals = []

        norm_name = _my_normcase(self.name)
        for repo_dir in self.dir.get_all_rdirs():
            try:
                node = repo_dir.entries[norm_name]
            except KeyError:
                node = repo_dir.file_on_disk(self.name)

            if node and node.exists() and \
                    (isinstance(node, File) or isinstance(node, Entry) \
                     or not node.is_derived()):
                retvals.append(node)

        return retvals


    def rstr(self):
        return str(self.rfile())

    def get_cachedir_csig(self):
        """
        Fetch a Node's content signature for purposes of computing
        another Node's cachesig.

        This is a wrapper around the normal get_csig() method that handles
        the somewhat obscure case of using CacheDir with the -n option.
        Any files that don't exist would normally be "built" by fetching
        them from the cache, but the normal get_csig() method will try
        to open up the local file, which doesn't exist because the -n
        option meant we didn't actually pull the file from cachedir.
        But since the file *does* actually exist in the cachedir, we
        can use its contents for the csig.
        """
        try:
            return self.cachedir_csig
        except AttributeError:
            pass

        cachedir, cachefile = self.get_build_env().get_CacheDir().cachepath(self)
        if not self.exists() and cachefile and os.path.exists(cachefile):
            self.cachedir_csig = SCons.Util.MD5filesignature(cachefile, \
                SCons.Node.FS.File.md5_chunksize * 1024)
        else:
            self.cachedir_csig = self.get_csig()
        return self.cachedir_csig

    def get_contents_sig(self):
        """
        A helper method for get_cachedir_bsig.

        It computes and returns the signature for this
        node's contents.
        """

        try:
            return self.contentsig
        except AttributeError:
            pass

        executor = self.get_executor()

        result = self.contentsig = SCons.Util.MD5signature(executor.get_contents())
        return result

    def get_cachedir_bsig(self):
        """
        Return the signature for a cached file, including
        its children.

        It adds the path of the cached file to the cache signature,
        because multiple targets built by the same action will all
        have the same build signature, and we have to differentiate
        them somehow.

        Signature should normally be string of hex digits.
        """
        try:
            return self.cachesig
        except AttributeError:
            pass

        # Collect signatures for all children
        children = self.children()
        sigs = [n.get_cachedir_csig() for n in children]

        # Append this node's signature...
        sigs.append(self.get_contents_sig())

        # ...and it's path
        sigs.append(self.get_internal_path())

        # Merge this all into a single signature
        result = self.cachesig = SCons.Util.MD5collect(sigs)
        return result

default_fs = None

def get_default_fs():
    global default_fs
    if not default_fs:
        default_fs = FS()
    return default_fs

class FileFinder(object):
    """
    """

    def __init__(self):
        self._memo = {}

    def filedir_lookup(self, p, fd=None):
        """
        A helper method for find_file() that looks up a directory for
        a file we're trying to find.  This only creates the Dir Node if
        it exists on-disk, since if the directory doesn't exist we know
        we won't find any files in it...  :-)

        It would be more compact to just use this as a nested function
        with a default keyword argument (see the commented-out version
        below), but that doesn't work unless you have nested scopes,
        so we define it here just so this work under Python 1.5.2.
        """
        if fd is None:
            fd = self.default_filedir
        dir, name = os.path.split(fd)
        drive, d = _my_splitdrive(dir)
        if not name and d[:1] in ('/', OS_SEP):
            #return p.fs.get_root(drive).dir_on_disk(name)
            return p.fs.get_root(drive)
        if dir:
            p = self.filedir_lookup(p, dir)
            if not p:
                return None
        norm_name = _my_normcase(name)
        try:
            node = p.entries[norm_name]
        except KeyError:
            return p.dir_on_disk(name)
        if isinstance(node, Dir):
            return node
        if isinstance(node, Entry):
            node.must_be_same(Dir)
            return node
        return None

    def _find_file_key(self, filename, paths, verbose=None):
        return (filename, paths)

    @SCons.Memoize.CountDictCall(_find_file_key)
    def find_file(self, filename, paths, verbose=None):
        """
        Find a node corresponding to either a derived file or a file that exists already.

        Only the first file found is returned, and none is returned if no file is found.

        filename: A filename to find
        paths: A list of directory path *nodes* to search in.  Can be represented as a list, a tuple, or a callable that is called with no arguments and returns the list or tuple.

        returns The node created from the found file.

        """
        memo_key = self._find_file_key(filename, paths)
        try:
            memo_dict = self._memo['find_file']
        except KeyError:
            memo_dict = {}
            self._memo['find_file'] = memo_dict
        else:
            try:
                return memo_dict[memo_key]
            except KeyError:
                pass

        if verbose and not callable(verbose):
            if not SCons.Util.is_String(verbose):
                verbose = "find_file"
            _verbose = u'  %s: ' % verbose
            verbose = lambda s: sys.stdout.write(_verbose + s)

        filedir, filename = os.path.split(filename)
        if filedir:
            self.default_filedir = filedir
            paths = [_f for _f in map(self.filedir_lookup, paths) if _f]

        result = None
        for dir in paths:
            if verbose:
                verbose("looking for '%s' in '%s' ...\n" % (filename, dir))
            node, d = dir.srcdir_find_file(filename)
            if node:
                if verbose:
                    verbose("... FOUND '%s' in '%s'\n" % (filename, d))
                result = node
                break

        memo_dict[memo_key] = result

        return result

find_file = FileFinder().find_file


def invalidate_node_memos(targets):
    """
    Invalidate the memoized values of all Nodes (files or directories)
    that are associated with the given entries. Has been added to
    clear the cache of nodes affected by a direct execution of an
    action (e.g.  Delete/Copy/Chmod). Existing Node caches become
    inconsistent if the action is run through Execute().  The argument
    `targets` can be a single Node object or filename, or a sequence
    of Nodes/filenames.
    """
    from traceback import extract_stack

    # First check if the cache really needs to be flushed. Only
    # actions run in the SConscript with Execute() seem to be
    # affected. XXX The way to check if Execute() is in the stacktrace
    # is a very dirty hack and should be replaced by a more sensible
    # solution.
    for f in extract_stack():
        if f[2] == 'Execute' and f[0][-14:] == 'Environment.py':
            break
    else:
        # Dont have to invalidate, so return
        return

    if not SCons.Util.is_List(targets):
        targets = [targets]

    for entry in targets:
        # If the target is a Node object, clear the cache. If it is a
        # filename, look up potentially existing Node object first.
        try:
            entry.clear_memoized_values()
        except AttributeError:
            # Not a Node object, try to look up Node by filename.  XXX
            # This creates Node objects even for those filenames which
            # do not correspond to an existing Node object.
            node = get_default_fs().Entry(entry)
            if node:
                node.clear_memoized_values()

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
