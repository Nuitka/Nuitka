"""SCons.Tool.gdc

Tool-specific initialization for the GDC compiler.
(https://github.com/D-Programming-GDC/GDC)

Developed by Russel Winder (russel@winder.org.uk)
2012-05-09 onwards

Compiler variables:
    DC - The name of the D compiler to use.  Defaults to gdc.
    DPATH - List of paths to search for import modules.
    DVERSIONS - List of version tags to enable when compiling.
    DDEBUG - List of debug tags to enable when compiling.

Linker related variables:
    LIBS - List of library files to link in.
    DLINK - Name of the linker to use.  Defaults to gdc.
    DLINKFLAGS - List of linker flags.

Lib tool variables:
    DLIB - Name of the lib tool to use.  Defaults to lib.
    DLIBFLAGS - List of flags to pass to the lib tool.
    LIBS - Same as for the linker. (libraries to pull into the .lib)
"""

#
# Copyright (c) 2001 - 2014 The SCons Foundation
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

__revision__ = "src/engine/SCons/Tool/gdc.py  2014/07/05 09:42:21 garyo"

import SCons.Action
import SCons.Defaults
import SCons.Tool

import SCons.Tool.DCommon


def generate(env):
    static_obj, shared_obj = SCons.Tool.createObjBuilders(env)

    static_obj.add_action('.d', SCons.Defaults.DAction)
    shared_obj.add_action('.d', SCons.Defaults.ShDAction)
    static_obj.add_emitter('.d', SCons.Defaults.StaticObjectEmitter)
    shared_obj.add_emitter('.d', SCons.Defaults.SharedObjectEmitter)

    env['DC'] = env.Detect('gdc')
    env['DCOM'] = '$DC $_DINCFLAGS $_DVERFLAGS $_DDEBUGFLAGS $_DFLAGS -c -o $TARGET $SOURCES'
    env['_DINCFLAGS'] = '$( ${_concat(DINCPREFIX, DPATH, DINCSUFFIX, __env__, RDirs, TARGET, SOURCE)}  $)'
    env['_DVERFLAGS'] = '$( ${_concat(DVERPREFIX, DVERSIONS, DVERSUFFIX, __env__)}  $)'
    env['_DDEBUGFLAGS'] = '$( ${_concat(DDEBUGPREFIX, DDEBUG, DDEBUGSUFFIX, __env__)} $)'
    env['_DFLAGS'] = '$( ${_concat(DFLAGPREFIX, DFLAGS, DFLAGSUFFIX, __env__)} $)'

    env['SHDC'] = '$DC'
    env['SHDCOM'] = '$SHDC $_DINCFLAGS $_DVERFLAGS $_DDEBUGFLAGS $_DFLAGS -fPIC -c -o $TARGET $SOURCES'

    env['DPATH'] = ['#/']
    env['DFLAGS'] = []
    env['DVERSIONS'] = []
    env['DDEBUG'] = []

    env['STATIC_AND_SHARED_OBJECTS_ARE_THE_SAME'] = 0

    if env['DC']:
        SCons.Tool.DCommon.addDPATHToEnv(env, env['DC'])

    env['DINCPREFIX'] = '-I'
    env['DINCSUFFIX'] = ''
    env['DVERPREFIX'] = '-version='
    env['DVERSUFFIX'] = ''
    env['DDEBUGPREFIX'] = '-debug='
    env['DDEBUGSUFFIX'] = ''
    env['DFLAGPREFIX'] = '-'
    env['DFLAGSUFFIX'] = ''
    env['DFILESUFFIX'] = '.d'

    env['DLINK'] = '$DC'
    env['DLINKFLAGS'] = SCons.Util.CLVar('')
    env['DLINKCOM'] = '$DLINK -o $TARGET $DLINKFLAGS $__RPATH $SOURCES $_LIBDIRFLAGS $_LIBFLAGS'

    env['SHDLINK'] = '$DC'
    env['SHDLINKFLAGS'] = SCons.Util.CLVar('$DLINKFLAGS -shared')
    env['SHDLINKCOM'] = '$DLINK -o $TARGET $DLINKFLAGS $__RPATH $SOURCES $_LIBDIRFLAGS $_LIBFLAGS'

    env['DLIB'] = 'lib' if env['PLATFORM'] == 'win32' else 'ar cr'
    env['DLIBCOM'] = '$DLIB $_DLIBFLAGS {} $TARGET $SOURCES $_DLINKLIBFLAGS'.format('-c' if env['PLATFORM'] == 'win32' else '')

    env['_DLIBFLAGS'] = '$( ${_concat(DLIBFLAGPREFIX, DLIBFLAGS, DLIBFLAGSUFFIX, __env__)} $)'

    env['DLIBFLAGPREFIX'] = '-'
    env['DLIBFLAGSUFFIX'] = ''
    env['DLINKFLAGPREFIX'] = '-'
    env['DLINKFLAGSUFFIX'] = ''

    # __RPATH is set to $_RPATH in the platform specification if that
    # platform supports it.
    env['RPATHPREFIX'] = '-Wl,-rpath='
    env['RPATHSUFFIX'] = ''
    env['_RPATH'] = '${_concat(RPATHPREFIX, RPATH, RPATHSUFFIX, __env__)}'

    SCons.Tool.createStaticLibBuilder(env)


def exists(env):
    return env.Detect('gdc')

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
