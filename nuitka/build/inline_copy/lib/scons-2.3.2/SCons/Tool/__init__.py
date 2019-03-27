"""SCons.Tool

SCons tool selection.

This looks for modules that define a callable object that can modify
a construction environment as appropriate for a given tool (or tool
chain).

Note that because this subsystem just *selects* a callable that can
modify a construction environment, it's possible for people to define
their own "tool specification" in an arbitrary callable function.  No
one needs to use or tie in to this subsystem in order to roll their own
tool definition.
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

__revision__ = "src/engine/SCons/Tool/__init__.py  2014/07/05 09:42:21 garyo"

import imp
import sys
import re
import os
import shutil

import SCons.Builder
import SCons.Errors
import SCons.Node.FS
import SCons.Scanner
import SCons.Scanner.C
import SCons.Scanner.Prog

DefaultToolpath=[]

CScanner = SCons.Scanner.C.CScanner()
ProgramScanner = SCons.Scanner.Prog.ProgramScanner()
SourceFileScanner = SCons.Scanner.Base({}, name='SourceFileScanner')

CSuffixes = [".c", ".C", ".cxx", ".cpp", ".c++", ".cc",
             ".h", ".H", ".hxx", ".hpp", ".hh",
             ".F", ".fpp", ".FPP",
             ".m", ".mm",
             ".S", ".spp", ".SPP", ".sx"]

DSuffixes = ['.d']

IDLSuffixes = [".idl", ".IDL"]

LaTeXSuffixes = [".tex", ".ltx", ".latex"]

for suffix in CSuffixes:
    SourceFileScanner.add_scanner(suffix, CScanner)

class Tool(object):
    def __init__(self, name, toolpath=[], **kw):
        self.name = name
        self.toolpath = toolpath + DefaultToolpath
        # remember these so we can merge them into the call
        self.init_kw = kw

        module = self._tool_module()
        self.generate = module.generate
        self.exists = module.exists
        if hasattr(module, 'options'):
            self.options = module.options

    def _tool_module(self):
        # TODO: Interchange zipimport with normal initilization for better error reporting
        oldpythonpath = sys.path
        sys.path = self.toolpath + sys.path

        try:
            try:
                file, path, desc = imp.find_module(self.name, self.toolpath)
                try:
                    return imp.load_module(self.name, file, path, desc)
                finally:
                    if file:
                        file.close()
            except ImportError, e:
                if str(e)!="No module named %s"%self.name:
                    raise SCons.Errors.EnvironmentError(e)
                try:
                    import zipimport
                except ImportError:
                    pass
                else:
                    for aPath in self.toolpath:
                        try:
                            importer = zipimport.zipimporter(aPath)
                            return importer.load_module(self.name)
                        except ImportError, e:
                            pass
        finally:
            sys.path = oldpythonpath

        full_name = 'SCons.Tool.' + self.name
        try:
            return sys.modules[full_name]
        except KeyError:
            try:
                smpath = sys.modules['SCons.Tool'].__path__
                try:
                    file, path, desc = imp.find_module(self.name, smpath)
                    module = imp.load_module(full_name, file, path, desc)
                    setattr(SCons.Tool, self.name, module)
                    if file:
                        file.close()
                    return module
                except ImportError, e:
                    if str(e)!="No module named %s"%self.name:
                        raise SCons.Errors.EnvironmentError(e)
                    try:
                        import zipimport
                        importer = zipimport.zipimporter( sys.modules['SCons.Tool'].__path__[0] )
                        module = importer.load_module(full_name)
                        setattr(SCons.Tool, self.name, module)
                        return module
                    except ImportError, e:
                        m = "No tool named '%s': %s" % (self.name, e)
                        raise SCons.Errors.EnvironmentError(m)
            except ImportError, e:
                m = "No tool named '%s': %s" % (self.name, e)
                raise SCons.Errors.EnvironmentError(m)

    def __call__(self, env, *args, **kw):
        if self.init_kw is not None:
            # Merge call kws into init kws;
            # but don't bash self.init_kw.
            if kw is not None:
                call_kw = kw
                kw = self.init_kw.copy()
                kw.update(call_kw)
            else:
                kw = self.init_kw
        env.Append(TOOLS = [ self.name ])
        if hasattr(self, 'options'):
            import SCons.Variables
            if 'options' not in env:
                from SCons.Script import ARGUMENTS
                env['options']=SCons.Variables.Variables(args=ARGUMENTS)
            opts=env['options']

            self.options(opts)
            opts.Update(env)

        self.generate(env, *args, **kw)

    def __str__(self):
        return self.name

##########################################################################
#  Create common executable program / library / object builders

def createProgBuilder(env):
    """This is a utility function that creates the Program
    Builder in an Environment if it is not there already.

    If it is already there, we return the existing one.
    """

    try:
        program = env['BUILDERS']['Program']
    except KeyError:
        import SCons.Defaults
        program = SCons.Builder.Builder(action = SCons.Defaults.LinkAction,
                                        emitter = '$PROGEMITTER',
                                        prefix = '$PROGPREFIX',
                                        suffix = '$PROGSUFFIX',
                                        src_suffix = '$OBJSUFFIX',
                                        src_builder = 'Object',
                                        target_scanner = ProgramScanner)
        env['BUILDERS']['Program'] = program

    return program

def createStaticLibBuilder(env):
    """This is a utility function that creates the StaticLibrary
    Builder in an Environment if it is not there already.

    If it is already there, we return the existing one.
    """

    try:
        static_lib = env['BUILDERS']['StaticLibrary']
    except KeyError:
        action_list = [ SCons.Action.Action("$ARCOM", "$ARCOMSTR") ]
        if env.Detect('ranlib'):
            ranlib_action = SCons.Action.Action("$RANLIBCOM", "$RANLIBCOMSTR")
            action_list.append(ranlib_action)

        static_lib = SCons.Builder.Builder(action = action_list,
                                           emitter = '$LIBEMITTER',
                                           prefix = '$LIBPREFIX',
                                           suffix = '$LIBSUFFIX',
                                           src_suffix = '$OBJSUFFIX',
                                           src_builder = 'StaticObject')
        env['BUILDERS']['StaticLibrary'] = static_lib
        env['BUILDERS']['Library'] = static_lib

    return static_lib

def VersionShLibLinkNames(version, libname, env):
    """Generate names of symlinks to the versioned shared library"""
    Verbose = False
    platform = env.subst('$PLATFORM')
    shlib_suffix = env.subst('$SHLIBSUFFIX')
    shlink_flags = SCons.Util.CLVar(env.subst('$SHLINKFLAGS'))

    linknames = []
    if version.count(".") != 2:
        # We need a version string of the form x.y.z to proceed
        # Several changes need to be made to support versions like x.y
        raise ValueError

    if platform == 'darwin':
        # For libfoo.x.y.z.dylib, linknames libfoo.so
        suffix_re = re.escape('.' + version + shlib_suffix)
        linkname = re.sub(suffix_re, shlib_suffix, libname)
        if Verbose:
            print "VersionShLibLinkNames: linkname = ",linkname
        linknames.append(linkname)
    elif platform == 'posix':
        if sys.platform.startswith('openbsd'):
            # OpenBSD uses x.y shared library versioning numbering convention
            # and doesn't use symlinks to backwards-compatible libraries
            return []
        # For libfoo.so.x.y.z, linknames libfoo.so libfoo.so.x.y libfoo.so.x
        suffix_re = re.escape(shlib_suffix + '.' + version)
        # First linkname has no version number
        linkname = re.sub(suffix_re, shlib_suffix, libname)
        if Verbose:
            print "VersionShLibLinkNames: linkname = ",linkname
        linknames.append(linkname)
        versionparts = version.split('.')
        major_name = linkname + "." + versionparts[0]
        minor_name = major_name + "." + versionparts[1]
        #Only add link for major_name
        #for linkname in [major_name, minor_name]:
        for linkname in [major_name, ]:
            if Verbose:
                print "VersionShLibLinkNames: linkname ",linkname, ", target ",libname
            linknames.append(linkname)
    # note: no Windows case here (win32 or cygwin);
    # MSVC doesn't support this type of versioned shared libs.
    # (could probably do something for MinGW though)
    return linknames

def VersionedSharedLibrary(target = None, source= None, env=None):
    """Build a shared library. If the environment has SHLIBVERSION
defined make a versioned shared library and create the appropriate
symlinks for the platform we are on"""
    Verbose = False
    try:
        version = env.subst('$SHLIBVERSION')
    except KeyError:
        version = None

    # libname includes the version number if one was given
    libname = target[0].name
    platform = env.subst('$PLATFORM')
    shlib_suffix = env.subst('$SHLIBSUFFIX')
    shlink_flags = SCons.Util.CLVar(env.subst('$SHLINKFLAGS'))
    if Verbose:
        print "VersionShLib: libname      = ",libname
        print "VersionShLib: platform     = ",platform
        print "VersionShLib: shlib_suffix = ",shlib_suffix
        print "VersionShLib: target = ",str(target[0])

    if version:
        # set the shared library link flags
        if platform == 'posix':
            shlink_flags += [ '-Wl,-Bsymbolic' ]
            # OpenBSD doesn't usually use SONAME for libraries
            if not sys.platform.startswith('openbsd'):
                # continue setup of shlink flags for all other POSIX systems
                suffix_re = re.escape(shlib_suffix + '.' + version)
                (major, age, revision) = version.split(".")
                # soname will have only the major version number in it
                soname = re.sub(suffix_re, shlib_suffix, libname) + '.' + major
                shlink_flags += [ '-Wl,-soname=%s' % soname ]
                if Verbose:
                    print " soname ",soname,", shlink_flags ",shlink_flags
        elif platform == 'cygwin':
            shlink_flags += [ '-Wl,-Bsymbolic',
                              '-Wl,--out-implib,${TARGET.base}.a' ]
        elif platform == 'darwin':
            shlink_flags += [ '-current_version', '%s' % version,
                              '-compatibility_version', '%s' % version,
                              '-undefined', 'dynamic_lookup' ]
        if Verbose:
            print "VersionShLib: shlink_flags = ",shlink_flags
        envlink = env.Clone()
        envlink['SHLINKFLAGS'] = shlink_flags
    else:
        envlink = env

    result = SCons.Defaults.ShLinkAction(target, source, envlink)

    if version:
        # here we need the full pathname so the links end up in the right directory
        libname = target[0].path
        linknames = VersionShLibLinkNames(version, libname, env)
        if Verbose:
            print "VerShLib: linknames ",linknames
        # Here we just need the file name w/o path as the target of the link
        lib_ver = target[0].name
        # make symlink of adjacent names in linknames
        for count in range(len(linknames)):
            linkname = linknames[count]
            if count > 0:
                try:
                    os.remove(lastlinkname)
                except:
                    pass
                os.symlink(os.path.basename(linkname),lastlinkname)
                if Verbose:
                    print "VerShLib: made sym link of %s -> %s" % (lastlinkname,linkname)
            lastlinkname = linkname
        # finish chain of sym links with link to the actual library
        if len(linknames)>0:
            try:
                os.remove(lastlinkname)
            except:
                pass
            os.symlink(lib_ver,lastlinkname)
            if Verbose:
                print "VerShLib: made sym link of %s -> %s" % (linkname, lib_ver)
    return result

# Fix http://scons.tigris.org/issues/show_bug.cgi?id=2903 :
# Ensure we still depend on SCons.Defaults.ShLinkAction command line which is $SHLINKCOM.
# This was tricky because we don't want changing LIBPATH to cause a rebuild, but
# changing other link args should.  LIBPATH has $( ... $) around it but until this
# fix, when the varlist was added to the build sig those ignored parts weren't getting
# ignored.
ShLibAction = SCons.Action.Action(VersionedSharedLibrary, None, varlist=['SHLINKCOM'])

def createSharedLibBuilder(env):
    """This is a utility function that creates the SharedLibrary
    Builder in an Environment if it is not there already.

    If it is already there, we return the existing one.
    """

    try:
        shared_lib = env['BUILDERS']['SharedLibrary']
    except KeyError:
        import SCons.Defaults
        action_list = [ SCons.Defaults.SharedCheck,
                        ShLibAction ]
        shared_lib = SCons.Builder.Builder(action = action_list,
                                           emitter = "$SHLIBEMITTER",
                                           prefix = '$SHLIBPREFIX',
                                           suffix = '$SHLIBSUFFIX',
                                           target_scanner = ProgramScanner,
                                           src_suffix = '$SHOBJSUFFIX',
                                           src_builder = 'SharedObject')
        env['BUILDERS']['SharedLibrary'] = shared_lib

    return shared_lib

def createLoadableModuleBuilder(env):
    """This is a utility function that creates the LoadableModule
    Builder in an Environment if it is not there already.

    If it is already there, we return the existing one.
    """

    try:
        ld_module = env['BUILDERS']['LoadableModule']
    except KeyError:
        import SCons.Defaults
        action_list = [ SCons.Defaults.SharedCheck,
                        SCons.Defaults.LdModuleLinkAction ]
        ld_module = SCons.Builder.Builder(action = action_list,
                                          emitter = "$LDMODULEEMITTER",
                                          prefix = '$LDMODULEPREFIX',
                                          suffix = '$LDMODULESUFFIX',
                                          target_scanner = ProgramScanner,
                                          src_suffix = '$SHOBJSUFFIX',
                                          src_builder = 'SharedObject')
        env['BUILDERS']['LoadableModule'] = ld_module

    return ld_module

def createObjBuilders(env):
    """This is a utility function that creates the StaticObject
    and SharedObject Builders in an Environment if they
    are not there already.

    If they are there already, we return the existing ones.

    This is a separate function because soooo many Tools
    use this functionality.

    The return is a 2-tuple of (StaticObject, SharedObject)
    """


    try:
        static_obj = env['BUILDERS']['StaticObject']
    except KeyError:
        static_obj = SCons.Builder.Builder(action = {},
                                           emitter = {},
                                           prefix = '$OBJPREFIX',
                                           suffix = '$OBJSUFFIX',
                                           src_builder = ['CFile', 'CXXFile'],
                                           source_scanner = SourceFileScanner,
                                           single_source = 1)
        env['BUILDERS']['StaticObject'] = static_obj
        env['BUILDERS']['Object'] = static_obj

    try:
        shared_obj = env['BUILDERS']['SharedObject']
    except KeyError:
        shared_obj = SCons.Builder.Builder(action = {},
                                           emitter = {},
                                           prefix = '$SHOBJPREFIX',
                                           suffix = '$SHOBJSUFFIX',
                                           src_builder = ['CFile', 'CXXFile'],
                                           source_scanner = SourceFileScanner,
                                           single_source = 1)
        env['BUILDERS']['SharedObject'] = shared_obj

    return (static_obj, shared_obj)

def createCFileBuilders(env):
    """This is a utility function that creates the CFile/CXXFile
    Builders in an Environment if they
    are not there already.

    If they are there already, we return the existing ones.

    This is a separate function because soooo many Tools
    use this functionality.

    The return is a 2-tuple of (CFile, CXXFile)
    """

    try:
        c_file = env['BUILDERS']['CFile']
    except KeyError:
        c_file = SCons.Builder.Builder(action = {},
                                       emitter = {},
                                       suffix = {None:'$CFILESUFFIX'})
        env['BUILDERS']['CFile'] = c_file

        env.SetDefault(CFILESUFFIX = '.c')

    try:
        cxx_file = env['BUILDERS']['CXXFile']
    except KeyError:
        cxx_file = SCons.Builder.Builder(action = {},
                                         emitter = {},
                                         suffix = {None:'$CXXFILESUFFIX'})
        env['BUILDERS']['CXXFile'] = cxx_file
        env.SetDefault(CXXFILESUFFIX = '.cc')

    return (c_file, cxx_file)

##########################################################################
#  Create common Java builders

def CreateJarBuilder(env):
    try:
        java_jar = env['BUILDERS']['Jar']
    except KeyError:
        fs = SCons.Node.FS.get_default_fs()
        jar_com = SCons.Action.Action('$JARCOM', '$JARCOMSTR')
        java_jar = SCons.Builder.Builder(action = jar_com,
                                         suffix = '$JARSUFFIX',
                                         src_suffix = '$JAVACLASSSUFIX',
                                         src_builder = 'JavaClassFile',
                                         source_factory = fs.Entry)
        env['BUILDERS']['Jar'] = java_jar
    return java_jar

def CreateJavaHBuilder(env):
    try:
        java_javah = env['BUILDERS']['JavaH']
    except KeyError:
        fs = SCons.Node.FS.get_default_fs()
        java_javah_com = SCons.Action.Action('$JAVAHCOM', '$JAVAHCOMSTR')
        java_javah = SCons.Builder.Builder(action = java_javah_com,
                                           src_suffix = '$JAVACLASSSUFFIX',
                                           target_factory = fs.Entry,
                                           source_factory = fs.File,
                                           src_builder = 'JavaClassFile')
        env['BUILDERS']['JavaH'] = java_javah
    return java_javah

def CreateJavaClassFileBuilder(env):
    try:
        java_class_file = env['BUILDERS']['JavaClassFile']
    except KeyError:
        fs = SCons.Node.FS.get_default_fs()
        javac_com = SCons.Action.Action('$JAVACCOM', '$JAVACCOMSTR')
        java_class_file = SCons.Builder.Builder(action = javac_com,
                                                emitter = {},
                                                #suffix = '$JAVACLASSSUFFIX',
                                                src_suffix = '$JAVASUFFIX',
                                                src_builder = ['JavaFile'],
                                                target_factory = fs.Entry,
                                                source_factory = fs.File)
        env['BUILDERS']['JavaClassFile'] = java_class_file
    return java_class_file

def CreateJavaClassDirBuilder(env):
    try:
        java_class_dir = env['BUILDERS']['JavaClassDir']
    except KeyError:
        fs = SCons.Node.FS.get_default_fs()
        javac_com = SCons.Action.Action('$JAVACCOM', '$JAVACCOMSTR')
        java_class_dir = SCons.Builder.Builder(action = javac_com,
                                               emitter = {},
                                               target_factory = fs.Dir,
                                               source_factory = fs.Dir)
        env['BUILDERS']['JavaClassDir'] = java_class_dir
    return java_class_dir

def CreateJavaFileBuilder(env):
    try:
        java_file = env['BUILDERS']['JavaFile']
    except KeyError:
        java_file = SCons.Builder.Builder(action = {},
                                          emitter = {},
                                          suffix = {None:'$JAVASUFFIX'})
        env['BUILDERS']['JavaFile'] = java_file
        env['JAVASUFFIX'] = '.java'
    return java_file

class ToolInitializerMethod(object):
    """
    This is added to a construction environment in place of a
    method(s) normally called for a Builder (env.Object, env.StaticObject,
    etc.).  When called, it has its associated ToolInitializer
    object search the specified list of tools and apply the first
    one that exists to the construction environment.  It then calls
    whatever builder was (presumably) added to the construction
    environment in place of this particular instance.
    """
    def __init__(self, name, initializer):
        """
        Note:  we store the tool name as __name__ so it can be used by
        the class that attaches this to a construction environment.
        """
        self.__name__ = name
        self.initializer = initializer

    def get_builder(self, env):
        """
	Returns the appropriate real Builder for this method name
	after having the associated ToolInitializer object apply
	the appropriate Tool module.
        """
        builder = getattr(env, self.__name__)

        self.initializer.apply_tools(env)

        builder = getattr(env, self.__name__)
        if builder is self:
            # There was no Builder added, which means no valid Tool
            # for this name was found (or possibly there's a mismatch
            # between the name we were called by and the Builder name
            # added by the Tool module).
            return None

        self.initializer.remove_methods(env)

        return builder

    def __call__(self, env, *args, **kw):
        """
        """
        builder = self.get_builder(env)
        if builder is None:
            return [], []
        return builder(*args, **kw)

class ToolInitializer(object):
    """
    A class for delayed initialization of Tools modules.

    Instances of this class associate a list of Tool modules with
    a list of Builder method names that will be added by those Tool
    modules.  As part of instantiating this object for a particular
    construction environment, we also add the appropriate
    ToolInitializerMethod objects for the various Builder methods
    that we want to use to delay Tool searches until necessary.
    """
    def __init__(self, env, tools, names):
        if not SCons.Util.is_List(tools):
            tools = [tools]
        if not SCons.Util.is_List(names):
            names = [names]
        self.env = env
        self.tools = tools
        self.names = names
        self.methods = {}
        for name in names:
            method = ToolInitializerMethod(name, self)
            self.methods[name] = method
            env.AddMethod(method)

    def remove_methods(self, env):
        """
        Removes the methods that were added by the tool initialization
        so we no longer copy and re-bind them when the construction
        environment gets cloned.
        """
        for method in self.methods.values():
            env.RemoveMethod(method)

    def apply_tools(self, env):
        """
	Searches the list of associated Tool modules for one that
	exists, and applies that to the construction environment.
        """
        for t in self.tools:
            tool = SCons.Tool.Tool(t)
            if tool.exists(env):
                env.Tool(tool)
                return

	# If we fall through here, there was no tool module found.
	# This is where we can put an informative error message
	# about the inability to find the tool.   We'll start doing
	# this as we cut over more pre-defined Builder+Tools to use
	# the ToolInitializer class.

def Initializers(env):
    ToolInitializer(env, ['install'], ['_InternalInstall', '_InternalInstallAs', '_InternalInstallVersionedLib'])
    def Install(self, *args, **kw):
        return self._InternalInstall(*args, **kw)
    def InstallAs(self, *args, **kw):
        return self._InternalInstallAs(*args, **kw)
    def InstallVersionedLib(self, *args, **kw):
        return self._InternalInstallVersionedLib(*args, **kw)
    env.AddMethod(Install)
    env.AddMethod(InstallAs)
    env.AddMethod(InstallVersionedLib)

def FindTool(tools, env):
    for tool in tools:
        t = Tool(tool)
        if t.exists(env):
            return tool
    return None

def FindAllTools(tools, env):
    def ToolExists(tool, env=env):
        return Tool(tool).exists(env)
    return list(filter (ToolExists, tools))

def tool_list(platform, env):

    other_plat_tools=[]
    # XXX this logic about what tool to prefer on which platform
    #     should be moved into either the platform files or
    #     the tool files themselves.
    # The search orders here are described in the man page.  If you
    # change these search orders, update the man page as well.
    if str(platform) == 'win32':
        "prefer Microsoft tools on Windows"
        linkers = ['mslink', 'gnulink', 'ilink', 'linkloc', 'ilink32' ]
        c_compilers = ['msvc', 'mingw', 'gcc', 'intelc', 'icl', 'icc', 'cc', 'bcc32' ]
        cxx_compilers = ['msvc', 'intelc', 'icc', 'g++', 'c++', 'bcc32' ]
        assemblers = ['masm', 'nasm', 'gas', '386asm' ]
        fortran_compilers = ['gfortran', 'g77', 'ifl', 'cvf', 'f95', 'f90', 'fortran']
        ars = ['mslib', 'ar', 'tlib']
        other_plat_tools = ['msvs']
    elif str(platform) == 'os2':
        "prefer IBM tools on OS/2"
        linkers = ['ilink', 'gnulink', ]#'mslink']
        c_compilers = ['icc', 'gcc',]# 'msvc', 'cc']
        cxx_compilers = ['icc', 'g++',]# 'msvc', 'c++']
        assemblers = ['nasm',]# 'masm', 'gas']
        fortran_compilers = ['ifl', 'g77']
        ars = ['ar',]# 'mslib']
    elif str(platform) == 'irix':
        "prefer MIPSPro on IRIX"
        linkers = ['sgilink', 'gnulink']
        c_compilers = ['sgicc', 'gcc', 'cc']
        cxx_compilers = ['sgic++', 'g++', 'c++']
        assemblers = ['as', 'gas']
        fortran_compilers = ['f95', 'f90', 'f77', 'g77', 'fortran']
        ars = ['sgiar']
    elif str(platform) == 'sunos':
        "prefer Forte tools on SunOS"
        linkers = ['sunlink', 'gnulink']
        c_compilers = ['suncc', 'gcc', 'cc']
        cxx_compilers = ['sunc++', 'g++', 'c++']
        assemblers = ['as', 'gas']
        fortran_compilers = ['sunf95', 'sunf90', 'sunf77', 'f95', 'f90', 'f77',
                             'gfortran', 'g77', 'fortran']
        ars = ['sunar']
    elif str(platform) == 'hpux':
        "prefer aCC tools on HP-UX"
        linkers = ['hplink', 'gnulink']
        c_compilers = ['hpcc', 'gcc', 'cc']
        cxx_compilers = ['hpc++', 'g++', 'c++']
        assemblers = ['as', 'gas']
        fortran_compilers = ['f95', 'f90', 'f77', 'g77', 'fortran']
        ars = ['ar']
    elif str(platform) == 'aix':
        "prefer AIX Visual Age tools on AIX"
        linkers = ['aixlink', 'gnulink']
        c_compilers = ['aixcc', 'gcc', 'cc']
        cxx_compilers = ['aixc++', 'g++', 'c++']
        assemblers = ['as', 'gas']
        fortran_compilers = ['f95', 'f90', 'aixf77', 'g77', 'fortran']
    elif str(platform) == 'darwin':
        "prefer GNU tools on Mac OS X, except for some linkers and IBM tools"
        linkers = ['applelink', 'gnulink']
        c_compilers = ['gcc', 'cc']
        cxx_compilers = ['g++', 'c++']
        assemblers = ['as']
        fortran_compilers = ['gfortran', 'f95', 'f90', 'g77']
        ars = ['ar']
    elif str(platform) == 'cygwin':
        "prefer GNU tools on Cygwin, except for a platform-specific linker"
        linkers = ['cyglink', 'mslink', 'ilink']
        c_compilers = ['gcc', 'msvc', 'intelc', 'icc', 'cc']
        cxx_compilers = ['g++', 'msvc', 'intelc', 'icc', 'c++']
        assemblers = ['gas', 'nasm', 'masm']
        ars = ['ar', 'mslib']
    else:
        "prefer GNU tools on all other platforms"
        linkers = ['gnulink', 'mslink', 'ilink']
        c_compilers = ['gcc', 'msvc', 'intelc', 'icc', 'cc']
        cxx_compilers = ['g++', 'msvc', 'intelc', 'icc', 'c++']
        assemblers = ['gas', 'nasm', 'masm']
        ars = ['ar', 'mslib']

    c_compiler = FindTool(c_compilers, env) or c_compilers[0]

    # XXX this logic about what tool provides what should somehow be
    #     moved into the tool files themselves.
    if c_compiler and c_compiler == 'mingw':
        # MinGW contains a linker, C compiler, C++ compiler,
        # Fortran compiler, archiver and assembler:
        cxx_compiler = None
        linker = None
        assembler = None
        ar = None
    else:
        # Don't use g++ if the C compiler has built-in C++ support:
        if c_compiler in ('msvc', 'intelc', 'icc'):
            cxx_compiler = None
        else:
            cxx_compiler = FindTool(cxx_compilers, env) or cxx_compilers[0]
        linker = FindTool(linkers, env) or linkers[0]
        assembler = FindTool(assemblers, env) or assemblers[0]
        ar = FindTool(ars, env) or ars[0]


    tools = [linker, c_compiler, cxx_compiler,
              assembler, ar]

    return [x for x in tools if x]

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:

