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
"""SCons.Tool.linkloc

Tool specification for the LinkLoc linker for the Phar Lap ETS embedded
operating system.

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

__revision__ = "src/engine/SCons/Tool/linkloc.py 5134 2010/08/16 23:02:40 bdeegan"

import os.path
import re

import SCons.Action
import SCons.Defaults
import SCons.Errors
import SCons.Tool
import SCons.Util

from SCons.Tool.MSCommon import msvs_exists, merge_default_version
from SCons.Tool.PharLapCommon import addPharLapPaths

_re_linker_command = re.compile(r'(\s)@\s*([^\s]+)')

def repl_linker_command(m):
    # Replaces any linker command file directives (e.g. "@foo.lnk") with
    # the actual contents of the file.
    try:
        f=open(m.group(2), "r")
        return m.group(1) + f.read()
    except IOError:
        # the linker should return an error if it can't
        # find the linker command file so we will remain quiet.
        # However, we will replace the @ with a # so we will not continue
        # to find it with recursive substitution
        return m.group(1) + '#' + m.group(2)

class LinklocGenerator(object):
    def __init__(self, cmdline):
        self.cmdline = cmdline

    def __call__(self, env, target, source, for_signature):
        if for_signature:
            # Expand the contents of any linker command files recursively
            subs = 1
            strsub = env.subst(self.cmdline, target=target, source=source)
            while subs:
                strsub, subs = _re_linker_command.subn(repl_linker_command, strsub)
            return strsub
        else:
            return "${TEMPFILE('" + self.cmdline + "')}"

def generate(env):
    """Add Builders and construction variables for ar to an Environment."""
    SCons.Tool.createSharedLibBuilder(env)
    SCons.Tool.createProgBuilder(env)

    env['SUBST_CMD_FILE'] = LinklocGenerator
    env['SHLINK']      = '$LINK'
    env['SHLINKFLAGS'] = SCons.Util.CLVar('$LINKFLAGS')
    env['SHLINKCOM']   = '${SUBST_CMD_FILE("$SHLINK $SHLINKFLAGS $_LIBDIRFLAGS $_LIBFLAGS -dll $TARGET $SOURCES")}'
    env['SHLIBEMITTER']= None
    env['LINK']        = "linkloc"
    env['LINKFLAGS']   = SCons.Util.CLVar('')
    env['LINKCOM']     = '${SUBST_CMD_FILE("$LINK $LINKFLAGS $_LIBDIRFLAGS $_LIBFLAGS -exe $TARGET $SOURCES")}'
    env['LIBDIRPREFIX']='-libpath '
    env['LIBDIRSUFFIX']=''
    env['LIBLINKPREFIX']='-lib '
    env['LIBLINKSUFFIX']='$LIBSUFFIX'

    # Set-up ms tools paths for default version
    merge_default_version(env)

    addPharLapPaths(env)

def exists(env):
    if msvs_exists():
        return env.Detect('linkloc')
    else:
        return 0

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
