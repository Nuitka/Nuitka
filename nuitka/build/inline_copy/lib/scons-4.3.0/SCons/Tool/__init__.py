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

"""SCons.Tool

SCons tool selection.

This looks for modules that define a callable object that can modify
a construction environment as appropriate for a given tool (or tool
chain).

Note that because this subsystem just *selects* a callable that can
modify a construction environment, it's possible for people to define
their own "tool specification" in an arbitrary callable function.  No
one needs to use or tie in to this subsystem in order to roll their own
tool specifications.
"""



import sys
import os
import importlib.util

import SCons.Builder
import SCons.Errors
import SCons.Node.FS
import SCons.Scanner
import SCons.Scanner.C
# Nuitka: Avoid ununused tools
# import SCons.Scanner.D
# import SCons.Scanner.LaTeX
import SCons.Scanner.Prog
# import SCons.Scanner.SWIG
from SCons.Tool.linkCommon import LibSymlinksActionFunction, LibSymlinksStrFun

DefaultToolpath = []

CScanner = SCons.Scanner.C.CScanner()
# Nuitka: Avoid ununused tools
# DScanner = SCons.Scanner.D.DScanner()
# LaTeXScanner = SCons.Scanner.LaTeX.LaTeXScanner()
# PDFLaTeXScanner = SCons.Scanner.LaTeX.PDFLaTeXScanner()
ProgramScanner = SCons.Scanner.Prog.ProgramScanner()
SourceFileScanner = SCons.Scanner.ScannerBase({}, name='SourceFileScanner')
# SWIGScanner = SCons.Scanner.SWIG.SWIGScanner()

CSuffixes = [".c", ".C", ".cxx", ".cpp", ".c++", ".cc",
             ".h", ".H", ".hxx", ".hpp", ".hh",
             ".F", ".fpp", ".FPP",
             ".m", ".mm",
             ".S", ".spp", ".SPP", ".sx"]

DSuffixes = ['.d']

IDLSuffixes = [".idl", ".IDL"]

LaTeXSuffixes = [".tex", ".ltx", ".latex"]

SWIGSuffixes = ['.i']

for suffix in CSuffixes:
    SourceFileScanner.add_scanner(suffix, CScanner)

# Nuitka: Avoid ununused tools
# for suffix in DSuffixes:
#     SourceFileScanner.add_scanner(suffix, DScanner)
#
# for suffix in SWIGSuffixes:
#    SourceFileScanner.add_scanner(suffix, SWIGScanner)

# FIXME: what should be done here? Two scanners scan the same extensions,
# but look for different files, e.g., "picture.eps" vs. "picture.pdf".
# The builders for DVI and PDF explicitly reference their scanners
# I think that means this is not needed???

# Nuitka: Avoid ununused tools
# for suffix in LaTeXSuffixes:
# for suffix in LaTeXSuffixes:
#    SourceFileScanner.add_scanner(suffix, LaTeXScanner)
#    SourceFileScanner.add_scanner(suffix, PDFLaTeXScanner)

# Tool aliases are needed for those tools whose module names also
# occur in the python standard library (This causes module shadowing and
# can break using python library functions under python3)  or if the current tool/file names
# are not legal module names (violate python's identifier rules or are
# python language keywords).
TOOL_ALIASES = {
    'gettext': 'gettext_tool',
    'clang++': 'clangxx',
    'as': 'asm',
}


class Tool:
    def __init__(self, name, toolpath=None, **kwargs):
        if toolpath is None:
            toolpath = []

        # Rename if there's a TOOL_ALIAS for this tool
        self.name = TOOL_ALIASES.get(name, name)
        self.toolpath = toolpath + DefaultToolpath
        # remember these so we can merge them into the call
        self.init_kw = kwargs

        module = self._tool_module()
        self.generate = module.generate
        self.exists = module.exists
        if hasattr(module, 'options'):
            self.options = module.options

    def _load_dotted_module_py2(self, short_name, full_name, searchpaths=None):
        import imp

        splitname = short_name.split('.')
        index = 0
        srchpths = searchpaths
        for item in splitname:
            file, path, desc = imp.find_module(item, srchpths)
            mod = imp.load_module(full_name, file, path, desc)
            srchpths = [path]
        return mod, file

    def _tool_module(self):
        oldpythonpath = sys.path
        sys.path = self.toolpath + sys.path
        # sys.stderr.write("Tool:%s\nPATH:%s\n"%(self.name,sys.path))

        # From: http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path/67692#67692
        # import importlib.util
        # spec = importlib.util.spec_from_file_location("module.name", "/path/to/file.py")
        # foo = importlib.util.module_from_spec(spec)
        # spec.loader.exec_module(foo)
        # foo.MyClass()
        # Py 3 code


        # sys.stderr.write("toolpath:%s\n" % self.toolpath)
        # sys.stderr.write("SCONS.TOOL path:%s\n" % sys.modules['SCons.Tool'].__path__)
        debug = False
        spec = None
        found_name = self.name
        add_to_scons_tools_namespace = False
        for path in self.toolpath:
            sepname = self.name.replace('.', os.path.sep)
            file_path = os.path.join(path, "%s.py" % sepname)
            file_package = os.path.join(path, sepname)

            if debug: sys.stderr.write("Trying:%s %s\n" % (file_path, file_package))

            if os.path.isfile(file_path):
                spec = importlib.util.spec_from_file_location(self.name, file_path)
                if debug: print("file_Path:%s FOUND" % file_path)
                break
            elif os.path.isdir(file_package):
                file_package = os.path.join(file_package, '__init__.py')
                spec = importlib.util.spec_from_file_location(self.name, file_package)
                if debug: print("PACKAGE:%s Found" % file_package)
                break

            else:
                continue

        if spec is None:
            if debug: sys.stderr.write("NO SPEC :%s\n" % self.name)
            spec = importlib.util.find_spec("." + self.name, package='SCons.Tool')
            if spec:
                found_name = 'SCons.Tool.' + self.name
                add_to_scons_tools_namespace = True
            if debug: sys.stderr.write("Spec Found? .%s :%s\n" % (self.name, spec))

        if spec is None:
            sconstools = os.path.normpath(sys.modules['SCons.Tool'].__path__[0])
            if self.toolpath:
                sconstools = ", ".join(self.toolpath) + ", " + sconstools
            error_string = "No tool module '%s' found in %s" % (self.name, sconstools)
            raise SCons.Errors.UserError(error_string)

        module = importlib.util.module_from_spec(spec)
        if module is None:
            if debug: print("MODULE IS NONE:%s" % self.name)
            error_string = "Tool module '%s' failed import" % self.name
            raise SCons.Errors.SConsEnvironmentError(error_string)

        # Don't reload a tool we already loaded.
        sys_modules_value = sys.modules.get(found_name, False)

        found_module = None
        if sys_modules_value and sys_modules_value.__file__ == spec.origin:
            found_module = sys.modules[found_name]
        else:
            # Not sure what to do in the case that there already
            # exists sys.modules[self.name] but the source file is
            # different.. ?
            module = spec.loader.load_module(spec.name)

            sys.modules[found_name] = module
            if add_to_scons_tools_namespace:
                # If we found it in SCons.Tool, then add it to the module
                setattr(SCons.Tool, self.name, module)

            found_module = module

        if found_module is not None:
            sys.path = oldpythonpath
            return found_module

        sys.path = oldpythonpath

        full_name = 'SCons.Tool.' + self.name
        try:
            return sys.modules[full_name]
        except KeyError:
            try:
                smpath = sys.modules['SCons.Tool'].__path__
                try:
                    module, file = self._load_dotted_module_py2(self.name, full_name, smpath)
                    setattr(SCons.Tool, self.name, module)
                    if file:
                        file.close()
                    return module
                except ImportError as e:
                    if str(e) != "No module named %s" % self.name:
                        raise SCons.Errors.SConsEnvironmentError(e)
                    try:
                        import zipimport
                        importer = zipimport.zipimporter(sys.modules['SCons.Tool'].__path__[0])
                        module = importer.load_module(full_name)
                        setattr(SCons.Tool, self.name, module)
                        return module
                    except ImportError as e:
                        m = "No tool named '%s': %s" % (self.name, e)
                        raise SCons.Errors.SConsEnvironmentError(m)
            except ImportError as e:
                m = "No tool named '%s': %s" % (self.name, e)
                raise SCons.Errors.SConsEnvironmentError(m)

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
        env.Append(TOOLS=[self.name])
        if hasattr(self, 'options'):
            import SCons.Variables
            if 'options' not in env:
                from SCons.Script import ARGUMENTS
                env['options'] = SCons.Variables.Variables(args=ARGUMENTS)
            opts = env['options']

            self.options(opts)
            opts.Update(env)

        self.generate(env, *args, **kw)

    def __str__(self):
        return self.name


LibSymlinksAction = SCons.Action.Action(LibSymlinksActionFunction, LibSymlinksStrFun)


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
        program = SCons.Builder.Builder(action=SCons.Defaults.LinkAction,
                                        emitter='$PROGEMITTER',
                                        prefix='$PROGPREFIX',
                                        suffix='$PROGSUFFIX',
                                        src_suffix='$OBJSUFFIX',
                                        src_builder='Object',
                                        target_scanner=ProgramScanner)
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
        action_list = [SCons.Action.Action("$ARCOM", "$ARCOMSTR")]
        if env.get('RANLIB', False) or env.Detect('ranlib'):
            ranlib_action = SCons.Action.Action("$RANLIBCOM", "$RANLIBCOMSTR")
            action_list.append(ranlib_action)

        static_lib = SCons.Builder.Builder(action=action_list,
                                           emitter='$LIBEMITTER',
                                           prefix='$LIBPREFIX',
                                           suffix='$LIBSUFFIX',
                                           src_suffix='$OBJSUFFIX',
                                           src_builder='StaticObject')
        env['BUILDERS']['StaticLibrary'] = static_lib
        env['BUILDERS']['Library'] = static_lib

    return static_lib


def createSharedLibBuilder(env, shlib_suffix='$_SHLIBSUFFIX'):
    """This is a utility function that creates the SharedLibrary
    Builder in an Environment if it is not there already.

    If it is already there, we return the existing one.

    Args:
        shlib_suffix: The suffix specified for the shared library builder

    """

    try:
        shared_lib = env['BUILDERS']['SharedLibrary']
    except KeyError:
        import SCons.Defaults
        action_list = [SCons.Defaults.SharedCheck,
                       SCons.Defaults.ShLinkAction,
                       LibSymlinksAction]
        shared_lib = SCons.Builder.Builder(action=action_list,
                                           emitter="$SHLIBEMITTER",
                                           prefix="$SHLIBPREFIX",
                                           suffix=shlib_suffix,
                                           target_scanner=ProgramScanner,
                                           src_suffix='$SHOBJSUFFIX',
                                           src_builder='SharedObject')
        env['BUILDERS']['SharedLibrary'] = shared_lib

    return shared_lib


def createLoadableModuleBuilder(env, loadable_module_suffix='$_LDMODULESUFFIX'):
    """This is a utility function that creates the LoadableModule
    Builder in an Environment if it is not there already.

    If it is already there, we return the existing one.

    Args:
        loadable_module_suffix: The suffix specified for the loadable module builder

    """

    try:
        ld_module = env['BUILDERS']['LoadableModule']
    except KeyError:
        import SCons.Defaults
        action_list = [SCons.Defaults.SharedCheck,
                       SCons.Defaults.LdModuleLinkAction,
                       LibSymlinksAction]
        ld_module = SCons.Builder.Builder(action=action_list,
                                          emitter="$LDMODULEEMITTER",
                                          prefix="$LDMODULEPREFIX",
                                          suffix=loadable_module_suffix,
                                          target_scanner=ProgramScanner,
                                          src_suffix='$SHOBJSUFFIX',
                                          src_builder='SharedObject')
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
        static_obj = SCons.Builder.Builder(action={},
                                           emitter={},
                                           prefix='$OBJPREFIX',
                                           suffix='$OBJSUFFIX',
                                           src_builder=['CFile', 'CXXFile'],
                                           source_scanner=SourceFileScanner,
                                           single_source=1)
        env['BUILDERS']['StaticObject'] = static_obj
        env['BUILDERS']['Object'] = static_obj

    try:
        shared_obj = env['BUILDERS']['SharedObject']
    except KeyError:
        shared_obj = SCons.Builder.Builder(action={},
                                           emitter={},
                                           prefix='$SHOBJPREFIX',
                                           suffix='$SHOBJSUFFIX',
                                           src_builder=['CFile', 'CXXFile'],
                                           source_scanner=SourceFileScanner,
                                           single_source=1)
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
        c_file = SCons.Builder.Builder(action={},
                                       emitter={},
                                       suffix={None: '$CFILESUFFIX'})
        env['BUILDERS']['CFile'] = c_file

        env.SetDefault(CFILESUFFIX='.c')

    try:
        cxx_file = env['BUILDERS']['CXXFile']
    except KeyError:
        cxx_file = SCons.Builder.Builder(action={},
                                         emitter={},
                                         suffix={None: '$CXXFILESUFFIX'})
        env['BUILDERS']['CXXFile'] = cxx_file
        env.SetDefault(CXXFILESUFFIX='.cc')

    return (c_file, cxx_file)


##########################################################################
#  Create common Java builders

def CreateJarBuilder(env):
    """The Jar builder expects a list of class files
    which it can package into a jar file.

    The jar tool provides an interface for passing other types
    of java files such as .java, directories or swig interfaces
    and will build them to class files in which it can package
    into the jar.
    """
    try:
        java_jar = env['BUILDERS']['JarFile']
    except KeyError:
        fs = SCons.Node.FS.get_default_fs()
        jar_com = SCons.Action.Action('$JARCOM', '$JARCOMSTR')
        java_jar = SCons.Builder.Builder(action=jar_com,
                                         suffix='$JARSUFFIX',
                                         src_suffix='$JAVACLASSSUFFIX',
                                         src_builder='JavaClassFile',
                                         source_factory=fs.Entry)
        env['BUILDERS']['JarFile'] = java_jar
    return java_jar


def CreateJavaHBuilder(env):
    try:
        java_javah = env['BUILDERS']['JavaH']
    except KeyError:
        fs = SCons.Node.FS.get_default_fs()
        java_javah_com = SCons.Action.Action('$JAVAHCOM', '$JAVAHCOMSTR')
        java_javah = SCons.Builder.Builder(action=java_javah_com,
                                           src_suffix='$JAVACLASSSUFFIX',
                                           target_factory=fs.Entry,
                                           source_factory=fs.File,
                                           src_builder='JavaClassFile')
        env['BUILDERS']['JavaH'] = java_javah
    return java_javah


def CreateJavaClassFileBuilder(env):
    try:
        java_class_file = env['BUILDERS']['JavaClassFile']
    except KeyError:
        fs = SCons.Node.FS.get_default_fs()
        javac_com = SCons.Action.Action('$JAVACCOM', '$JAVACCOMSTR')
        java_class_file = SCons.Builder.Builder(action=javac_com,
                                                emitter={},
                                                # suffix = '$JAVACLASSSUFFIX',
                                                src_suffix='$JAVASUFFIX',
                                                src_builder=['JavaFile'],
                                                target_factory=fs.Entry,
                                                source_factory=fs.File)
        env['BUILDERS']['JavaClassFile'] = java_class_file
    return java_class_file


def CreateJavaClassDirBuilder(env):
    try:
        java_class_dir = env['BUILDERS']['JavaClassDir']
    except KeyError:
        fs = SCons.Node.FS.get_default_fs()
        javac_com = SCons.Action.Action('$JAVACCOM', '$JAVACCOMSTR')
        java_class_dir = SCons.Builder.Builder(action=javac_com,
                                               emitter={},
                                               target_factory=fs.Dir,
                                               source_factory=fs.Dir)
        env['BUILDERS']['JavaClassDir'] = java_class_dir
    return java_class_dir


def CreateJavaFileBuilder(env):
    try:
        java_file = env['BUILDERS']['JavaFile']
    except KeyError:
        java_file = SCons.Builder.Builder(action={},
                                          emitter={},
                                          suffix={None: '$JAVASUFFIX'})
        env['BUILDERS']['JavaFile'] = java_file
        env['JAVASUFFIX'] = '.java'
    return java_file


class ToolInitializerMethod:
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


class ToolInitializer:
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

    return list(filter(ToolExists, tools))


def tool_list(platform, env):
    other_plat_tools = []
    # XXX this logic about what tool to prefer on which platform
    #     should be moved into either the platform files or
    #     the tool files themselves.
    # The search orders here are described in the man page.  If you
    # change these search orders, update the man page as well.
    if str(platform) == 'win32':
        "prefer Microsoft tools on Windows"
        linkers = ['mslink', 'gnulink', 'ilink', 'linkloc', 'ilink32']
        c_compilers = ['msvc', 'mingw', 'gcc', 'intelc', 'icl', 'icc', 'cc', 'bcc32']
        cxx_compilers = ['msvc', 'intelc', 'icc', 'g++', 'cxx', 'bcc32']
        assemblers = ['masm', 'nasm', 'gas', '386asm']
        fortran_compilers = ['gfortran', 'g77', 'ifl', 'cvf', 'f95', 'f90', 'fortran']
        ars = ['mslib', 'ar', 'tlib']
        # Nuitka: Do not use "midl" tool.
        other_plat_tools = ['msvs']
    elif str(platform) == 'os2':
        "prefer IBM tools on OS/2"
        linkers = ['ilink', 'gnulink', ]  # 'mslink']
        c_compilers = ['icc', 'gcc', ]  # 'msvc', 'cc']
        cxx_compilers = ['icc', 'g++', ]  # 'msvc', 'cxx']
        assemblers = ['nasm', ]  # 'masm', 'gas']
        fortran_compilers = ['ifl', 'g77']
        ars = ['ar', ]  # 'mslib']
    elif str(platform) == 'irix':
        "prefer MIPSPro on IRIX"
        linkers = ['sgilink', 'gnulink']
        c_compilers = ['sgicc', 'gcc', 'cc']
        cxx_compilers = ['sgicxx', 'g++', 'cxx']
        assemblers = ['as', 'gas']
        fortran_compilers = ['f95', 'f90', 'f77', 'g77', 'fortran']
        ars = ['sgiar']
    elif str(platform) == 'sunos':
        "prefer Forte tools on SunOS"
        linkers = ['sunlink', 'gnulink']
        c_compilers = ['suncc', 'gcc', 'cc']
        cxx_compilers = ['suncxx', 'g++', 'cxx']
        assemblers = ['as', 'gas']
        fortran_compilers = ['sunf95', 'sunf90', 'sunf77', 'f95', 'f90', 'f77',
                             'gfortran', 'g77', 'fortran']
        ars = ['sunar']
    elif str(platform) == 'hpux':
        "prefer aCC tools on HP-UX"
        linkers = ['hplink', 'gnulink']
        c_compilers = ['hpcc', 'gcc', 'cc']
        cxx_compilers = ['hpcxx', 'g++', 'cxx']
        assemblers = ['as', 'gas']
        fortran_compilers = ['f95', 'f90', 'f77', 'g77', 'fortran']
        ars = ['ar']
    elif str(platform) == 'aix':
        "prefer AIX Visual Age tools on AIX"
        linkers = ['aixlink', 'gnulink']
        c_compilers = ['aixcc', 'gcc', 'cc']
        cxx_compilers = ['aixcxx', 'g++', 'cxx']
        assemblers = ['as', 'gas']
        fortran_compilers = ['f95', 'f90', 'aixf77', 'g77', 'fortran']
        ars = ['ar']
    elif str(platform) == 'darwin':
        "prefer GNU tools on Mac OS X, except for some linkers and IBM tools"
        linkers = ['applelink', 'gnulink']
        c_compilers = ['gcc', 'cc']
        cxx_compilers = ['g++', 'cxx']
        assemblers = ['as']
        fortran_compilers = ['gfortran', 'f95', 'f90', 'g77']
        ars = ['ar']
    elif str(platform) == 'cygwin':
        "prefer GNU tools on Cygwin, except for a platform-specific linker"
        linkers = ['cyglink', 'mslink', 'ilink']
        c_compilers = ['gcc', 'msvc', 'intelc', 'icc', 'cc']
        cxx_compilers = ['g++', 'msvc', 'intelc', 'icc', 'cxx']
        assemblers = ['gas', 'nasm', 'masm']
        fortran_compilers = ['gfortran', 'g77', 'ifort', 'ifl', 'f95', 'f90', 'f77']
        ars = ['ar', 'mslib']
    else:
        "prefer GNU tools on all other platforms"
        linkers = ['gnulink', 'ilink']
        c_compilers = ['gcc', 'intelc', 'icc', 'cc']
        cxx_compilers = ['g++', 'intelc', 'icc', 'cxx']
        assemblers = ['gas', 'nasm', 'masm']
        fortran_compilers = ['gfortran', 'g77', 'ifort', 'ifl', 'f95', 'f90', 'f77']
        ars = ['ar', ]

    if not str(platform) == 'win32':
        other_plat_tools += ['m4', 'rpm']

    c_compiler = FindTool(c_compilers, env) or c_compilers[0]

    # XXX this logic about what tool provides what should somehow be
    #     moved into the tool files themselves.
    if c_compiler and c_compiler == 'mingw':
        # MinGW contains a linker, C compiler, C++ compiler,
        # Fortran compiler, archiver and assembler:
        cxx_compiler = None
        linker = None
        assembler = None
        fortran_compiler = None
        ar = None
    else:
        # Don't use g++ if the C compiler has built-in C++ support:
        if c_compiler in ('msvc', 'intelc', 'icc'):
            cxx_compiler = None
        else:
            cxx_compiler = FindTool(cxx_compilers, env) or cxx_compilers[0]
        linker = FindTool(linkers, env) or linkers[0]
        # Nuitka: Avoid ununused tools
        # assembler = FindTool(assemblers, env) or assemblers[0]
        # fortran_compiler = FindTool(fortran_compilers, env) or fortran_compilers[0]
        # ar = FindTool(ars, env) or ars[0]
        assembler = None
        fortran_compiler = None
        ar = None

    d_compilers = ['dmd', 'ldc', 'gdc']
    # Nuitka: Avoid ununused tools
    # d_compiler = FindTool(d_compilers, env) or d_compilers[0]
    d_compiler = []

    other_tools = FindAllTools(other_plat_tools, env)
# Nuitka: Avoid ununused tools + [
    #     # TODO: merge 'install' into 'filesystem' and
    #     # make 'filesystem' the default
    #     'filesystem',
    #     # Parser generators
    #     'lex', 'yacc',
    #     # Foreign function interface
    #     'rpcgen', 'swig',
    #     # Java
    #     'jar', 'javac', 'javah', 'rmic',
    #     # TeX
    #     'dvipdf', 'dvips', 'gs',
    #     'tex', 'latex', 'pdflatex', 'pdftex',
    #     # Archivers
    #     'tar', 'zip',
    #     # File builders (text)
    #     'textfile',
    # ], env)

    tools = [
        linker,
        c_compiler,
        cxx_compiler,
        fortran_compiler,
        assembler,
        ar,
        d_compiler,
    ] + other_tools

    return [x for x in tools if x]


def find_program_path(env, key_program, default_paths=None):
    """
    Find the location of a tool using various means.

    Mainly for windows where tools aren't all installed in /usr/bin, etc.

    :param env: Current Construction Environment.
    :param key_program: Tool to locate.
    :param default_paths: List of additional paths this tool might be found in.
    """
    # First search in the SCons path
    path = env.WhereIs(key_program)
    if path:
        return path

    # Then in the OS path
    path = SCons.Util.WhereIs(key_program)
    if path:
        return path

    # Finally, add the defaults and check again. Do not change
    # ['ENV']['PATH'] permananetly, the caller can do that if needed.
    if default_paths is None:
        return path
    save_path = env['ENV']['PATH']
    for p in default_paths:
        env.AppendENVPath('PATH', p)
    path = env.WhereIs(key_program)
    env['ENV']['PATH'] = save_path
    return path

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
