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
"""SCons.Tool.filesystem

Tool-specific initialization for the filesystem tools.

There normally shouldn't be any need to import this module directly.
It will usually be imported through the generic SCons.Tool.Tool()
selection method.
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

__revision__ = "src/engine/SCons/Tool/filesystem.py 5134 2010/08/16 23:02:40 bdeegan"

import SCons
from SCons.Tool.install import copyFunc

copyToBuilder, copyAsBuilder = None, None

def copyto_emitter(target, source, env):
    """ changes the path of the source to be under the target (which
    are assumed to be directories.
    """
    n_target = []

    for t in target:
        n_target = n_target + [t.File( str( s ) ) for s in source]

    return (n_target, source)

def copy_action_func(target, source, env):
    assert( len(target) == len(source) ), "\ntarget: %s\nsource: %s" %(list(map(str, target)),list(map(str, source)))

    for t, s in zip(target, source):
        if copyFunc(t.get_path(), s.get_path(), env):
            return 1

    return 0

def copy_action_str(target, source, env):
    return env.subst_target_source(env['COPYSTR'], 0, target, source)

copy_action = SCons.Action.Action( copy_action_func, copy_action_str )

def generate(env):
    try:
        env['BUILDERS']['CopyTo']
        env['BUILDERS']['CopyAs']
    except KeyError, e:
        global copyToBuilder
        if copyToBuilder is None:
            copyToBuilder = SCons.Builder.Builder(
                             action         = copy_action,
                             target_factory = env.fs.Dir,
                             source_factory = env.fs.Entry,
                             multi          = 1,
                             emitter        = [ copyto_emitter, ] )

        global copyAsBuilder
        if copyAsBuilder is None:
            copyAsBuilder = SCons.Builder.Builder(
                             action         = copy_action,
                             target_factory = env.fs.Entry,
                             source_factory = env.fs.Entry )

        env['BUILDERS']['CopyTo'] = copyToBuilder
        env['BUILDERS']['CopyAs'] = copyAsBuilder

        env['COPYSTR'] = 'Copy file(s): "$SOURCES" to "$TARGETS"'

def exists(env):
    return 1

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
