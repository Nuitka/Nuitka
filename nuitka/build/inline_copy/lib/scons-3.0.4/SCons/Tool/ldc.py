from __future__ import print_function

"""SCons.Tool.ldc

Tool-specific initialization for the LDC compiler.
(https://github.com/ldc-developers/ldc)

Developed by Russel Winder (russel@winder.org.uk)
2012-05-09 onwards

Compiler variables:
    DC - The name of the D compiler to use.  Defaults to ldc2.
    DPATH - List of paths to search for import modules.
    DVERSIONS - List of version tags to enable when compiling.
    DDEBUG - List of debug tags to enable when compiling.

Linker related variables:
    LIBS - List of library files to link in.
    DLINK - Name of the linker to use.  Defaults to ldc2.
    DLINKFLAGS - List of linker flags.

Lib tool variables:
    DLIB - Name of the lib tool to use.  Defaults to lib.
    DLIBFLAGS - List of flags to pass to the lib tool.
    LIBS - Same as for the linker. (libraries to pull into the .lib)
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
#

__revision__ = "src/engine/SCons/Tool/ldc.py 3a41ed6b288cee8d085373ad7fa02894e1903864 2019-01-23 17:30:35 bdeegan"

import os
import subprocess

import SCons.Action
import SCons.Builder
import SCons.Defaults
import SCons.Scanner.D
import SCons.Tool

import SCons.Tool.DCommon as DCommon


def generate(env):
    static_obj, shared_obj = SCons.Tool.createObjBuilders(env)

    static_obj.add_action('.d', SCons.Defaults.DAction)
    shared_obj.add_action('.d', SCons.Defaults.ShDAction)
    static_obj.add_emitter('.d', SCons.Defaults.StaticObjectEmitter)
    shared_obj.add_emitter('.d', SCons.Defaults.SharedObjectEmitter)

    env['DC'] = env.Detect('ldc2') or 'ldc2'
    env['DCOM'] = '$DC $_DINCFLAGS $_DVERFLAGS $_DDEBUGFLAGS $_DFLAGS -c -of=$TARGET $SOURCES'
    env['_DINCFLAGS'] = '${_concat(DINCPREFIX, DPATH, DINCSUFFIX, __env__, RDirs, TARGET, SOURCE)}'
    env['_DVERFLAGS'] = '${_concat(DVERPREFIX, DVERSIONS, DVERSUFFIX, __env__)}'
    env['_DDEBUGFLAGS'] = '${_concat(DDEBUGPREFIX, DDEBUG, DDEBUGSUFFIX, __env__)}'
    env['_DFLAGS'] = '${_concat(DFLAGPREFIX, DFLAGS, DFLAGSUFFIX, __env__)}'

    env['SHDC'] = '$DC'
    env['SHDCOM'] = '$DC $_DINCFLAGS $_DVERFLAGS $_DDEBUGFLAGS $_DFLAGS -c -relocation-model=pic -of=$TARGET $SOURCES'

    env['DPATH'] = ['#/']
    env['DFLAGS'] = []
    env['DVERSIONS'] = []
    env['DDEBUG'] = []

    if env['DC']:
        DCommon.addDPATHToEnv(env, env['DC'])

    env['DINCPREFIX'] = '-I='
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
    env['DLINKCOM'] = '$DLINK -of=$TARGET $DLINKFLAGS $__DRPATH $SOURCES $_DLIBDIRFLAGS $_DLIBFLAGS'

    env['SHDLINK'] = '$DC'
    env['SHDLINKFLAGS'] = SCons.Util.CLVar('$DLINKFLAGS -shared -defaultlib=phobos2-ldc')

    env['SHDLINKCOM'] = '$DLINK -of=$TARGET $SHDLINKFLAGS $__SHDLIBVERSIONFLAGS $__DRPATH $SOURCES $_DLIBDIRFLAGS $_DLIBFLAGS -L-ldruntime-ldc'

    env['DLIBLINKPREFIX'] = '' if env['PLATFORM'] == 'win32' else '-L-l'
    env['DLIBLINKSUFFIX'] = '.lib' if env['PLATFORM'] == 'win32' else ''
    # env['_DLIBFLAGS'] = '${_concat(DLIBLINKPREFIX, LIBS, DLIBLINKSUFFIX, __env__, RDirs, TARGET, SOURCE)}'
    env['_DLIBFLAGS'] = '${_stripixes(DLIBLINKPREFIX, LIBS, DLIBLINKSUFFIX, LIBPREFIXES, LIBSUFFIXES,  __env__)}'

    env['DLIBDIRPREFIX'] = '-L-L'
    env['DLIBDIRSUFFIX'] = ''
    env['_DLIBDIRFLAGS'] = '${_concat(DLIBDIRPREFIX, LIBPATH, DLIBDIRSUFFIX, __env__, RDirs, TARGET, SOURCE)}'

    env['DLIB'] = 'lib' if env['PLATFORM'] == 'win32' else 'ar cr'
    env['DLIBCOM'] = '$DLIB $_DLIBFLAGS {0}$TARGET $SOURCES $_DLIBFLAGS'.format('-c ' if env['PLATFORM'] == 'win32' else '')

    # env['_DLIBFLAGS'] = '${_concat(DLIBFLAGPREFIX, DLIBFLAGS, DLIBFLAGSUFFIX, __env__)}'

    env['DLIBFLAGPREFIX'] = '-'
    env['DLIBFLAGSUFFIX'] = ''

    # __RPATH is set to $_RPATH in the platform specification if that
    # platform supports it.
    env['DRPATHPREFIX'] = '-L-Wl,-rpath,' if env['PLATFORM'] == 'darwin' else '-L-rpath='
    env['DRPATHSUFFIX'] = ''
    env['_DRPATH'] = '${_concat(DRPATHPREFIX, RPATH, DRPATHSUFFIX, __env__)}'

    # Support for versioned libraries
    env['_SHDLIBVERSIONFLAGS'] = '$SHDLIBVERSIONFLAGS -L-soname=$_SHDLIBSONAME'
    env['_SHDLIBSONAME'] = '${DShLibSonameGenerator(__env__,TARGET)}'
    # NOTE: this is a quick hack, the soname will only work if there is
    # c/c++ linker loaded which provides callback for the ShLibSonameGenerator
    env['DShLibSonameGenerator'] = SCons.Tool.ShLibSonameGenerator
    # NOTE: this is only for further reference, currently $SHDLIBVERSION does
    # not work, the user must use $SHLIBVERSION
    env['SHDLIBVERSION'] = '$SHLIBVERSION'
    env['SHDLIBVERSIONFLAGS'] = []

    env['BUILDERS']['ProgramAllAtOnce'] = SCons.Builder.Builder(
        action='$DC $_DINCFLAGS $_DVERFLAGS $_DDEBUGFLAGS $_DFLAGS -of=$TARGET $DLINKFLAGS $__DRPATH $SOURCES $_DLIBDIRFLAGS $_DLIBFLAGS',
        emitter=DCommon.allAtOnceEmitter,
    )


def exists(env):
    return env.Detect('ldc2')


# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
