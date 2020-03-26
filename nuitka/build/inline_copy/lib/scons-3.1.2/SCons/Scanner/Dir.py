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

__revision__ = "src/engine/SCons/Scanner/Dir.py bee7caf9defd6e108fc2998a2520ddb36a967691 2019-12-17 02:07:09 bdeegan"

import SCons.Node.FS
import SCons.Scanner

def only_dirs(nodes):
    is_Dir = lambda n: isinstance(n.disambiguate(), SCons.Node.FS.Dir)
    return [node for node in nodes if is_Dir(node)]

def DirScanner(**kw):
    """Return a prototype Scanner instance for scanning
    directories for on-disk files"""
    kw['node_factory'] = SCons.Node.FS.Entry
    kw['recursive'] = only_dirs
    return SCons.Scanner.Base(scan_on_disk, "DirScanner", **kw)

def DirEntryScanner(**kw):
    """Return a prototype Scanner instance for "scanning"
    directory Nodes for their in-memory entries"""
    kw['node_factory'] = SCons.Node.FS.Entry
    kw['recursive'] = None
    return SCons.Scanner.Base(scan_in_memory, "DirEntryScanner", **kw)

skip_entry = {}

skip_entry_list = [
   '.',
   '..',
   '.sconsign',
   # Used by the native dblite.py module.
   '.sconsign.dblite',
   # Used by dbm and dumbdbm.
   '.sconsign.dir',
   # Used by dbm.
   '.sconsign.pag',
   # Used by dumbdbm.
   '.sconsign.dat',
   '.sconsign.bak',
   # Used by some dbm emulations using Berkeley DB.
   '.sconsign.db',
]

for skip in skip_entry_list:
    skip_entry[skip] = 1
    skip_entry[SCons.Node.FS._my_normcase(skip)] = 1

do_not_scan = lambda k: k not in skip_entry

def scan_on_disk(node, env, path=()):
    """
    Scans a directory for on-disk files and directories therein.

    Looking up the entries will add these to the in-memory Node tree
    representation of the file system, so all we have to do is just
    that and then call the in-memory scanning function.
    """
    try:
        flist = node.fs.listdir(node.get_abspath())
    except (IOError, OSError):
        return []
    e = node.Entry
    for f in  filter(do_not_scan, flist):
        # Add ./ to the beginning of the file name so if it begins with a
        # '#' we don't look it up relative to the top-level directory.
        e('./' + f)
    return scan_in_memory(node, env, path)

def scan_in_memory(node, env, path=()):
    """
    "Scans" a Node.FS.Dir for its in-memory entries.
    """
    try:
        entries = node.entries
    except AttributeError:
        # It's not a Node.FS.Dir (or doesn't look enough like one for
        # our purposes), which can happen if a target list containing
        # mixed Node types (Dirs and Files, for example) has a Dir as
        # the first entry.
        return []
    entry_list = sorted(filter(do_not_scan, list(entries.keys())))
    return [entries[n] for n in entry_list]

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
