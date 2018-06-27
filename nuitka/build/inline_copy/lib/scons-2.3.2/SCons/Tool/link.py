"""SCons.Tool.link

Tool-specific initialization for the generic Posix linker.

There normally shouldn't be any need to import this module directly.
It will usually be imported through the generic SCons.Tool.Tool()
selection method.

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

__revision__ = "src/engine/SCons/Tool/link.py  2014/07/05 09:42:21 garyo"

import re

import SCons.Defaults
import SCons.Tool
import SCons.Util
import SCons.Warnings

cplusplus = __import__('c++', globals(), locals(), [])

def isfortran(env, source): return False
def isD(env,source): return False

issued_mixed_link_warning = False

def smart_link(source, target, env, for_signature):
    has_cplusplus = cplusplus.iscplusplus(source)
    has_fortran = isfortran(env, source)
    has_d = isD(env, source)
    if has_cplusplus and has_fortran and not has_d:
        global issued_mixed_link_warning
        if not issued_mixed_link_warning:
            msg = "Using $CXX to link Fortran and C++ code together.\n\t" + \
              "This may generate a buggy executable if the '%s'\n\t" + \
              "compiler does not know how to deal with Fortran runtimes."
            SCons.Warnings.warn(SCons.Warnings.FortranCxxMixWarning,
                                msg % env.subst('$CXX'))
            issued_mixed_link_warning = True
        return '$CXX'
    elif has_d:
        env['LINKCOM'] = env['DLINKCOM']
        env['SHLINKCOM'] = env['SHDLINKCOM']
        return '$DC'
    elif has_fortran:
        return '$FORTRAN'
    elif has_cplusplus:
        return '$CXX'
    return '$CC'

def shlib_emitter(target, source, env):
    Verbose = False
    platform = env.subst('$PLATFORM')
    for tgt in target:
        tgt.attributes.shared = 1
    try:
        # target[0] comes in as libtest.so. Add the version extensions
        version = env.subst('$SHLIBVERSION')
        if version:
            version_names = shlib_emitter_names(target, source, env)
            # change the name of the target to include the version number
            target[0].name = version_names[0]
            for name in version_names:
                env.SideEffect(name, target[0])
                env.Clean(target[0], name)
                if Verbose:
                    print "shlib_emitter: add side effect - ",name
    except KeyError:
        version = None
    return (target, source)

def shlib_emitter_names(target, source, env):
    """Return list of file names that are side effects for a versioned library build. The first name in the list is the new name for the target"""
    Verbose = False
    platform = env.subst('$PLATFORM')
    version_names = []
    try:
        # target[0] comes in as libtest.so. Add the version extensions
        version = env.subst('$SHLIBVERSION')
        if version.count(".") != 2:
            # We need a version of the form x.y.z to proceed
            raise ValueError
        if version:
            if platform == 'posix':
                versionparts = version.split('.')
                name = target[0].name
                # generate library name with the version number
                version_name = target[0].name + '.' + version
                if Verbose:
                    print "shlib_emitter_names: target is ", version_name
                    print "shlib_emitter_names: side effect: ", name
                # add version_name to list of names to be a Side effect
                version_names.append(version_name)
                if Verbose:
                    print "shlib_emitter_names: versionparts ",versionparts
                for ver in versionparts[0:-1]:
                    name = name + '.' + ver
                    if Verbose:
                        print "shlib_emitter_names: side effect: ", name
                    # add name to list of names to be a Side effect
                    version_names.append(name)
            elif platform == 'darwin':
                shlib_suffix = env.subst('$SHLIBSUFFIX')
                name = target[0].name
                # generate library name with the version number
                suffix_re = re.escape(shlib_suffix)
                version_name = re.sub(suffix_re, '.' + version + shlib_suffix, name)
                if Verbose:
                    print "shlib_emitter_names: target is ", version_name
                    print "shlib_emitter_names: side effect: ", name
                # add version_name to list of names to be a Side effect
                version_names.append(version_name)
            elif platform == 'cygwin':
                shlib_suffix = env.subst('$SHLIBSUFFIX')
                name = target[0].name
                # generate library name with the version number
                suffix_re = re.escape(shlib_suffix)
                version_name = re.sub(suffix_re, '-' + re.sub('\.', '-', version) + shlib_suffix, name)
                if Verbose:
                    print "shlib_emitter_names: target is ", version_name
                    print "shlib_emitter_names: side effect: ", name
                # add version_name to list of names to be a Side effect
                version_names.append(version_name)

    except KeyError:
        version = None
    return version_names

def generate(env):
    """Add Builders and construction variables for gnulink to an Environment."""
    SCons.Tool.createSharedLibBuilder(env)
    SCons.Tool.createProgBuilder(env)

    env['SHLINK']      = '$LINK'
    env['SHLINKFLAGS'] = SCons.Util.CLVar('$LINKFLAGS -shared')
    env['SHLINKCOM']   = '$SHLINK -o $TARGET $SHLINKFLAGS $__RPATH $SOURCES $_LIBDIRFLAGS $_LIBFLAGS'
    # don't set up the emitter, cause AppendUnique will generate a list
    # starting with None :-(
    env.Append(SHLIBEMITTER = [shlib_emitter])
    env['SMARTLINK']   = smart_link
    env['LINK']        = "$SMARTLINK"
    env['LINKFLAGS']   = SCons.Util.CLVar('')
    # __RPATH is only set to something ($_RPATH typically) on platforms that support it.
    env['LINKCOM']     = '$LINK -o $TARGET $LINKFLAGS $__RPATH $SOURCES $_LIBDIRFLAGS $_LIBFLAGS'
    env['LIBDIRPREFIX']='-L'
    env['LIBDIRSUFFIX']=''
    env['_LIBFLAGS']='${_stripixes(LIBLINKPREFIX, LIBS, LIBLINKSUFFIX, LIBPREFIXES, LIBSUFFIXES, __env__)}'
    env['LIBLINKPREFIX']='-l'
    env['LIBLINKSUFFIX']=''

    if env['PLATFORM'] == 'hpux':
        env['SHLIBSUFFIX'] = '.sl'
    elif env['PLATFORM'] == 'aix':
        env['SHLIBSUFFIX'] = '.a'

    # For most platforms, a loadable module is the same as a shared
    # library.  Platforms which are different can override these, but
    # setting them the same means that LoadableModule works everywhere.
    SCons.Tool.createLoadableModuleBuilder(env)
    env['LDMODULE'] = '$SHLINK'
    # don't set up the emitter, cause AppendUnique will generate a list
    # starting with None :-(
    env.Append(LDMODULEEMITTER='$SHLIBEMITTER')
    env['LDMODULEPREFIX'] = '$SHLIBPREFIX'
    env['LDMODULESUFFIX'] = '$SHLIBSUFFIX'
    env['LDMODULEFLAGS'] = '$SHLINKFLAGS'
    env['LDMODULECOM'] = '$LDMODULE -o $TARGET $LDMODULEFLAGS $__RPATH $SOURCES $_LIBDIRFLAGS $_LIBFLAGS'



def exists(env):
    # This module isn't really a Tool on its own, it's common logic for
    # other linkers.
    return None

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
