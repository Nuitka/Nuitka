#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
""" Command line options of Nuitka.

These provide only the optparse options to use, and the mechanic to actually
do it, but updating and checking module "nuitka.Options" values is not in
the scope, to make sure it can be used without.

Note: This is using "optparse", because "argparse" is only Python 2.7 and
higher, and we still support Python 2.6 due to the RHELs still being used,
and despite the long deprecation, it's in every later release.
"""

import os
import sys
from optparse import SUPPRESS_HELP, OptionGroup, OptionParser

from nuitka.utils import Utils
from nuitka.Version import getNuitkaVersion

# Indicator if we were called as "nuitka-run" in which case we assume some
# other defaults and work a bit different with parameters.
is_nuitka_run = os.path.basename(sys.argv[0]).lower().endswith("-run")

if not is_nuitka_run:
    usage = "usage: %prog [--module] [--run] [options] main_module.py"
else:
    usage = "usage: %prog [options] main_module.py"

parser = OptionParser(
    usage=usage,
    version="\n".join(
        (
            getNuitkaVersion(),
            "Python: " + sys.version.split("\n")[0],
            "Executable: " + sys.executable,
            "OS: " + Utils.getOS(),
            "Arch: " + Utils.getArchitecture(),
        )
    ),
)

parser.add_option(
    "--module",
    action="store_false",
    dest="executable",
    default=True,
    help="""\
Create an extension module executable instead of a program. Defaults to off.""",
)

parser.add_option(
    "--standalone",
    action="store_true",
    dest="is_standalone",
    default=False,
    help="""\
Enable standalone mode for output. This allows you to transfer the created binary
to other machines without it using an existing Python installation. This also
means it will become big. It implies these option: "--recurse-all". You may also
want to use "--python-flag=no_site" to avoid the "site.py" module, which can save
a lot of code dependencies. Defaults to off.""",
)

parser.add_option(
    "--onefile",
    action="store_true",
    dest="is_onefile",
    default=False,
    help="""\
In case of standalone mode, enable single file mode. This means not a folder,
but a compressed executable is created and used. Experimental at this time,
and not supported on all OSes. Defaults to off.""",
)


if os.name == "nt":
    parser.add_option(
        "--python-arch",
        action="store",
        dest="python_arch",
        choices=("x86", "x86_64"),
        default=None,
        help="""\
Architecture of Python to use. One of "x86" or "x86_64".
Defaults to what you run Nuitka with (currently "%s")."""
        % (Utils.getArchitecture()),
    )

parser.add_option(
    "--python-debug",
    action="store_true",
    dest="python_debug",
    default=None,
    help="""\
Use debug version or not. Default uses what you are using to run Nuitka, most
likely a non-debug version.""",
)

parser.add_option(
    "--python-flag",
    action="append",
    dest="python_flags",
    default=[],
    help="""\
Python flags to use. Default uses what you are using to run Nuitka, this
enforces a specific mode. These are options that also exist to standard
Python executable. Currently supported: "-S" (alias "nosite"),
"static_hashes" (do not use hash randomization), "no_warnings" (do not
give Python runtime warnings), "-O" (alias "noasserts"). Default empty.""",
)

parser.add_option(
    "--python-for-scons",
    action="store",
    dest="python_scons",
    default=None,
    help="""\
If using Python3.3 or Python3.4, provide the path of a Python binary to use
for Scons. Otherwise Nuitka can use what you run Nuitka with or a "scons"
binary that is found in PATH, or a Python installation from Windows registry.""",
)

parser.add_option(
    "--warn-implicit-exceptions",
    action="store_true",
    dest="warn_implicit_exceptions",
    default=False,
    help="""\
Enable warnings for implicit exceptions detected at compile time.""",
)

parser.add_option(
    "--warn-unusual-code",
    action="store_true",
    dest="warn_unusual_code",
    default=False,
    help="""\
Enable warnings for unusual code detected at compile time.""",
)

parser.add_option(
    "--assume-yes-for-downloads",
    action="store_true",
    dest="assume_yes_for_downloads",
    default=False,
    help="""\
Allow Nuitka to download code if necessary, e.g. dependency walker on Windows.""",
)


include_group = OptionGroup(
    parser, "Control the inclusion of modules and packages in result."
)

include_group.add_option(
    "--include-package",
    action="append",
    dest="include_packages",
    metavar="PACKAGE",
    default=[],
    help="""\
Include a whole package. Give as a Python namespace, e.g. ``some_package.sub_package``
and Nuitka will then find it and include it and all the modules found below that
disk location in the binary or extension module it creates, and make it available
for import by the code. Default empty.""",
)

include_group.add_option(
    "--include-module",
    action="append",
    dest="include_modules",
    metavar="MODULE",
    default=[],
    help="""\
Include a single module. Give as a Python namespace, e.g. ``some_package.some_module``
and Nuitka will then find it and include it in the binary or extension module
it creates, and make it available for import by the code. Default empty.""",
)

include_group.add_option(
    "--include-plugin-directory",
    action="append",
    dest="recurse_extra",
    metavar="MODULE/PACKAGE",
    default=[],
    help="""\
Include the content of that directory, no matter if it's used by the given main
program in a visible form. Overrides all other recursion options. Can be given
multiple times. Default empty.""",
)

include_group.add_option(
    "--include-plugin-files",
    action="append",
    dest="recurse_extra_files",
    metavar="PATTERN",
    default=[],
    help="""\
Include into files matching the PATTERN. Overrides all other follow options.
Can be given multiple times. Default empty.""",
)

include_group.add_option(
    "--prefer-source-code",
    action="store_true",
    dest="prefer_source_code",
    default=None,
    help="""\
For already compiled extension modules, where there is both a source file and an
extension module, normally the extension module is used, but it should be better
to compile the module from available source code for best performance. If not
desired, there is --no-prefer-source-code to disable warnings about it. Default
off.""",
)
include_group.add_option(
    "--no-prefer-source-code",
    action="store_false",
    dest="prefer_source_code",
    default=None,
    help=SUPPRESS_HELP,
)


parser.add_option_group(include_group)

follow_group = OptionGroup(parser, "Control the following into imported modules")


follow_group.add_option(
    "--follow-stdlib",
    action="store_true",
    dest="recurse_stdlib",
    default=False,
    help="""\
Also descend into imported modules from standard library. This will increase
the compilation time by a lot. Defaults to off.""",
)

follow_group.add_option(
    "--nofollow-imports",
    action="store_true",
    dest="recurse_none",
    default=False,
    help="""\
When --recurse-none is used, do not descend into any imported modules at all,
overrides all other recursion options. Defaults to off.""",
)

follow_group.add_option(
    "--follow-imports",
    action="store_true",
    dest="recurse_all",
    default=False,
    help="""\
When --follow-imports is used, attempt to descend into all imported modules.
Defaults to off.""",
)

follow_group.add_option(
    "--follow-import-to",
    action="append",
    dest="recurse_modules",
    metavar="MODULE/PACKAGE",
    default=[],
    help="""\
Follow to that module if used, or if a package, to the whole package. Can be given
multiple times. Default empty.""",
)

follow_group.add_option(
    "--nofollow-import-to",
    action="append",
    dest="recurse_not_modules",
    metavar="MODULE/PACKAGE",
    default=[],
    help="""\
Do not follow to that module name even if used, or if a package name, to the
whole package in any case, overrides all other options. Can be given multiple
times. Default empty.""",
)

parser.add_option_group(follow_group)


data_group = OptionGroup(parser, "Data files for standalone/onefile mode")

data_group.add_option(
    "--include-package-data",
    action="append",
    dest="package_data",
    metavar="PACKAGE_DATA",
    default=[],
    help="""\
Include data files of the given package name. Can use patterns. By default
Nuitka does not unless hard coded and vital for operation of a package. This
will include all non-DLL, non-extension modules in the distribution. Default
empty.""",
)

data_group.add_option(
    "--include-data-file",
    action="append",
    dest="data_files",
    metavar="DATA_FILES",
    default=[],
    help="""\
Include data files by filenames in the distribution. Could use patterns for
use in glob, if specifying a directory with trailing slash. An example would
be --include-data-file=/etc/somefile.txt=etc/somefile.txt for plain file copy,
and you can copy multiple like --include-data-file=/etc/*.txt:etc/ with a
trailing slash required to use the pattern. Default empty.""",
)


parser.add_option_group(data_group)


execute_group = OptionGroup(parser, "Immediate execution after compilation")

execute_group.add_option(
    "--run",
    action="store_true",
    dest="immediate_execution",
    default=is_nuitka_run,
    help="""\
Execute immediately the created binary (or import the compiled module).
Defaults to %s."""
    % ("on" if is_nuitka_run else "off"),
)

execute_group.add_option(
    "--debugger",
    "--gdb",
    action="store_true",
    dest="debugger",
    default=False,
    help="""\
Execute inside "gdb" to automatically get a stack trace.
Defaults to off.""",
)

execute_group.add_option(
    "--execute-with-pythonpath",
    action="store_true",
    dest="keep_pythonpath",
    default=False,
    help="""\
When immediately executing the created binary (--execute), don't reset
PYTHONPATH. When all modules are successfully included, you ought to not need
PYTHONPATH anymore.""",
)

parser.add_option_group(execute_group)

dump_group = OptionGroup(parser, "Dump options for internal tree")

dump_group.add_option(
    "--xml",
    action="store_true",
    dest="dump_xml",
    default=False,
    help="Dump the final result of optimization as XML, then exit.",
)


parser.add_option_group(dump_group)


codegen_group = OptionGroup(parser, "Code generation choices")

codegen_group.add_option(
    "--full-compat",
    action="store_false",
    dest="improved",
    default=True,
    help="""\
Enforce absolute compatibility with CPython. Do not even allow minor
deviations from CPython behavior, e.g. not having better tracebacks
or exception messages which are not really incompatible, but only
different. This is intended for tests only and should not be used
for normal use.""",
)

codegen_group.add_option(
    "--file-reference-choice",
    action="store",
    dest="file_reference_mode",
    choices=("original", "runtime", "frozen"),
    default=None,
    help="""\
Select what value "__file__" is going to be. With "runtime" (default for
standalone binary mode and module mode), the created binaries and modules,
use the location of themselves to deduct the value of "__file__". Included
packages pretend to be in directories below that location. This allows you
to include data files in deployments. If you merely seek acceleration, it's
better for you to use the "original" value, where the source files location
will be used. With "frozen" a notation "<frozen module_name>" is used. For
compatibility reasons, the "__file__" value will always have ".py" suffix
independent of what it really is.""",
)

parser.add_option_group(codegen_group)

output_group = OptionGroup(parser, "Output choices")

output_group.add_option(
    "-o",
    action="store",
    dest="output_filename",
    metavar="FILENAME",
    default=None,
    help="""\
Specify how the executable should be named. For extension modules there is no
choice, also not for standalone mode and using it will be an error. This may
include path information that needs to exist though. Defaults to %s on this
platform.
"""
    % "<program_name>"
    + (".exe" if Utils.getOS() == "Windows" else ".bin"),
)

output_group.add_option(
    "--output-dir",
    action="store",
    dest="output_dir",
    metavar="DIRECTORY",
    default="",
    help="""\
Specify where intermediate and final output files should be put. The DIRECTORY
will be populated with C files, object files, etc.
Defaults to current directory.
""",
)

output_group.add_option(
    "--remove-output",
    action="store_true",
    dest="remove_build",
    default=False,
    help="""\
Removes the build directory after producing the module or exe file.
Defaults to off.""",
)

output_group.add_option(
    "--no-pyi-file",
    action="store_false",
    dest="pyi_file",
    default=True,
    help="""\
Do not create a ".pyi" file for extension modules created by Nuitka. This is
used to detect implicit imports.
Defaults to off.""",
)

parser.add_option_group(output_group)


debug_group = OptionGroup(parser, "Debug features")

debug_group.add_option(
    "--debug",
    action="store_true",
    dest="debug",
    default=False,
    help="""\
Executing all self checks possible to find errors in Nuitka, do not use for
production. Defaults to off.""",
)

debug_group.add_option(
    "--unstripped",
    action="store_true",
    dest="unstripped",
    default=False,
    help="""\
Keep debug info in the resulting object file for better debugger interaction.
Defaults to off.""",
)

debug_group.add_option(
    "--profile",
    action="store_true",
    dest="profile",
    default=False,
    help="""\
Enable vmprof based profiling of time spent. Not working currently. Defaults to off.""",
)

debug_group.add_option(
    "--graph",
    action="store_true",
    dest="graph",
    default=False,
    help="""\
Create graph of optimization process. Defaults to off.""",
)

debug_group.add_option(
    "--trace-execution",
    action="store_true",
    dest="trace_execution",
    default=False,
    help="""\
Traced execution output, output the line of code before executing it.
Defaults to off.""",
)

debug_group.add_option(
    "--recompile-c-only",
    action="store_true",
    dest="recompile_c_only",
    default=False,
    help="""\
This is not incremental compilation, but for Nuitka development only. Takes
existing files and simply compile them as C again. Allows compiling edited
C files for quick debugging changes to the generated source, e.g. to see if
code is passed by, values output, etc, Defaults to off. Depends on compiling
Python source to determine which files it should look at.""",
)

debug_group.add_option(
    "--generate-c-only",
    action="store_true",
    dest="generate_c_only",
    default=False,
    help="""\
Generate only C source code, and do not compile it to binary or module. This
is for debugging and code coverage analysis that doesn't waste CPU. Defaults to
off. Do not think you can use this directly.""",
)

debug_group.add_option(
    "--experimental",
    action="append",
    dest="experimental",
    default=[],
    help="""\
Use features declared as 'experimental'. May have no effect if no experimental
features are present in the code. Uses secret tags (check source) per
experimented feature.""",
)

debug_group.add_option(
    "--explain-imports",
    action="store_true",
    dest="explain_imports",
    default=False,
    help=SUPPRESS_HELP,
)

if os.name == "nt":
    debug_group.add_option(
        "--disable-dll-dependency-cache",
        action="store_true",
        dest="no_dependency_cache",
        default=False,
        help="""\
Disable the dependency walker cache. Will result in much longer times to create
the distribution folder, but might be used in case the cache is suspect to cause
errors.
""",
    )

    debug_group.add_option(
        "--force-dll-dependency-cache-update",
        action="store_true",
        dest="update_dependency_cache",
        default=False,
        help="""\
For an update of the dependency walker cache. Will result in much longer times
to create the distribution folder, but might be used in case the cache is suspect
to cause errors or known to need an update.
""",
    )

# This is for testing framework, "coverage.py" hates to loose the process. And
# we can use it to make sure it's not done unknowingly.
parser.add_option(
    "--must-not-re-execute",
    action="store_false",
    dest="allow_reexecute",
    default=True,
    help=SUPPRESS_HELP,
)


parser.add_option_group(debug_group)

c_compiler_group = OptionGroup(parser, "Backend C compiler choice")


c_compiler_group.add_option(
    "--clang",
    action="store_true",
    dest="clang",
    default=False,
    help="""\
Enforce the use of clang. On Windows this requires a working Visual
Studio version to piggy back on. Defaults to off.""",
)

if os.name == "nt":
    c_compiler_group.add_option(
        "--mingw64",
        action="store_true",
        dest="mingw64",
        default=False,
        help="""\
Enforce the use of MinGW64 on Windows. Defaults to off.""",
    )

    c_compiler_group.add_option(
        "--msvc",
        action="store",
        dest="msvc",
        default=None,
        help="""\
Enforce the use of specific MSVC version on Windows. Allowed values
are e.g. 14.0, specify an illegal value for a list of installed compilers,
beware that only latest MSVC is really supported.

Defaults to the most recent version.""",
    )

c_compiler_group.add_option(
    "-j",
    "--jobs",
    action="store",
    dest="jobs",
    metavar="N",
    default=Utils.getCoreCount(),
    help="""\
Specify the allowed number of parallel C compiler jobs. Defaults to the
system CPU count.""",
)

c_compiler_group.add_option(
    "--lto",
    action="store_true",
    dest="lto",
    default=False,
    help="""\
Use link time optimizations if available and usable (MSVC or gcc 4.6 and higher).
Defaults to off.""",
)

parser.add_option_group(c_compiler_group)

tracing_group = OptionGroup(parser, "Tracing features")

tracing_group.add_option(
    "--quiet",
    action="store_true",
    dest="quiet",
    default=False,
    help="""\
Disable all information outputs, but show warnings.
Defaults to off.""",
)

tracing_group.add_option(
    "--show-scons",
    action="store_true",
    dest="show_scons",
    default=False,
    help="""\
Operate Scons in non-quiet mode, showing the executed commands.
Defaults to off.""",
)

tracing_group.add_option(
    "--show-progress",
    action="store_true",
    dest="show_progress",
    default=False,
    help="""Provide progress information and statistics.
Defaults to off.""",
)

tracing_group.add_option(
    "--show-memory",
    action="store_true",
    dest="show_memory",
    default=False,
    help="""Provide memory information and statistics.
Defaults to off.""",
)


tracing_group.add_option(
    "--show-modules",
    action="store_true",
    dest="show_inclusion",
    default=False,
    help="""\
Provide information for included modules and DLLs
Defaults to off.""",
)

tracing_group.add_option(
    "--show-modules-output",
    action="store",
    dest="show_inclusion_output",
    default=None,
    help="""\
Where to output --show-modules, should be a filename. Default is standard output.""",
)

tracing_group.add_option(
    "--verbose",
    action="store_true",
    dest="verbose",
    default=False,
    help="""\
Output details of actions taken, esp. in optimizations. Can become a lot.
Defaults to off.""",
)

tracing_group.add_option(
    "--verbose-output",
    action="store",
    dest="verbose_output",
    default=None,
    help="""\
Where to output --verbose, should be a filename. Default is standard output.""",
)

parser.add_option_group(tracing_group)

windows_group = OptionGroup(parser, "Windows specific controls")

windows_group.add_option(
    "--windows-dependency-tool",
    action="store",
    dest="dependency_tool",
    default="depends.exe",
    help="""\
When compiling for Windows, use this dependency tool. Defaults to %default,
other allowed value is 'pefile'.""",
)

windows_group.add_option(
    "--windows-disable-console",
    action="store_true",
    dest="win_disable_console",
    default=False,
    help="""\
When compiling for Windows, disable the console window. Defaults to off.""",
)

windows_group.add_option(
    "--windows-icon-from-ico",
    action="append",
    dest="icon_path",
    metavar="ICON_PATH",
    default=[],
    help="Add executable icon. Can be given multiple times for different resolutions.",
)

windows_group.add_option(
    "--windows-icon-from-exe",
    action="store",
    dest="icon_exe_path",
    metavar="ICON_EXE_PATH",
    default=None,
    help="Copy executable icons from this existing executable (Windows only).",
)

windows_group.add_option(
    "--windows-uac-admin",
    action="store_true",
    dest="windows_uac_admin",
    metavar="WINDOWS_UAC_ADMIN",
    default=False,
    help="Request Windows User Control, to grant admin rights on execution. (Windows only). Defaults to off.",
)

windows_group.add_option(
    "--windows-uac-uiaccess",
    action="store_true",
    dest="windows_uac_uiaccess",
    metavar="WINDOWS_UAC_UIACCESS",
    default=False,
    help="""\
Request Windows User Control, to enforce running from a few folders only, remote
desktop access. (Windows only). Defaults to off.""",
)

windows_group.add_option(
    "--windows-company-name",
    action="store",
    dest="windows_company_name",
    metavar="WINDOWS_COMPANY_NAME",
    default=None,
    help="""\
Name of the company to use in Windows Version information.

One of file or product version is required, when a version resource needs to be
added, e.g. to specify product name, or company name. Defaults to unused.""",
)

windows_group.add_option(
    "--windows-product-name",
    action="store",
    dest="windows_product_name",
    metavar="WINDOWS_PRODUCT_NAME",
    default=None,
    help="""\
Name of the product to use in Windows Version information. Defaults to base
filename of the binary.""",
)


windows_group.add_option(
    "--windows-file-version",
    action="store",
    dest="windows_file_version",
    metavar="WINDOWS_FILE_VERSION",
    default=None,
    help="""\
File version to use in Windows Version information. Must be a sequence of
up to 4 numbers, nothing else allowed.
One of file or product version is required, when a version resource needs to be
added, e.g. to specify product name, or company name. Defaults to unused.""",
)

windows_group.add_option(
    "--windows-product-version",
    action="store",
    dest="windows_product_version",
    metavar="WINDOWS_PRODUCT_VERSION",
    default=None,
    help="""\
Product version to use in Windows Version information. Must be a sequence of
up to 4 numbers, nothing else allowed.
One of file or product version is required, when a version resource needs to be
added, e.g. to specify product name, or company name. Defaults to unused.""",
)

windows_group.add_option(
    "--windows-file-description",
    action="store",
    dest="windows_file_description",
    metavar="WINDOWS_FILE_DESCRIPTION",
    default=None,
    help="""\
Description of the file use in Windows Version information.

One of file or product version is required, when a version resource needs to be
added, e.g. to specify product name, or company name. Defaults to nonsense.""",
)

windows_group.add_option(
    "--windows-onefile-tempdir",
    action="store_true",
    dest="is_windows_onefile_tempdir",
    metavar="WINDOWS_ONEFILE_TEMPDIR",
    default=False,
    help="""\
Use temporary folder rather than company AppData. Defaults to off.""",
)


parser.add_option_group(windows_group)

linux_group = OptionGroup(parser, "Linux specific controls")

linux_group.add_option(
    "--linux-onefile-icon",
    action="append",
    dest="icon_path",
    metavar="ICON_PATH",
    default=[],
    help="Add executable icon for onefile binary to use. Can be given only one time. Defaults to ",
)

parser.add_option_group(linux_group)

plugin_group = OptionGroup(parser, "Plugin control")

plugin_group.add_option(
    "--plugin-enable",
    "--enable-plugin",
    action="append",
    dest="plugins_enabled",
    default=[],
    help="""\
Enabled plugins. Must be plug-in names. Use --plugin-list to query the
full list and exit. Default empty.""",
)

plugin_group.add_option(
    "--plugin-disable",
    "--disable-plugin",
    action="append",
    dest="plugins_disabled",
    default=[],
    help="""\
Disabled plugins. Must be plug-in names. Use --plugin-list to query the
full list and exit. Default empty.""",
)

plugin_group.add_option(
    "--plugin-no-detection",
    action="store_false",
    dest="detect_missing_plugins",
    default=True,
    help="""\
Plugins can detect if they might be used, and the you can disable the warning
via --plugin-disable=plugin-that-warned, or you can use this option to disable
the mechanism entirely, which also speeds up compilation slightly of course as
this detection code is run in vain once you are certain of which plug-ins to
use. Defaults to off.""",
)

plugin_group.add_option(
    "--plugin-list",
    action="store_true",
    dest="list_plugins",
    default=False,
    help="""\
Show list of all available plugins and exit. Defaults to off.""",
)


parser.add_option_group(plugin_group)

plugin_group.add_option(
    "--user-plugin",
    action="append",
    dest="user_plugins",
    default=[],
    help="The file name of user plugin. Can be given multiple times. Default empty.",
)


def _considerPluginOptions(logger):
    # Recursive dependency on plugins during parsing of command line.
    from nuitka.plugins.Plugins import (
        addPluginCommandLineOptions,
        addUserPluginCommandLineOptions,
    )

    for arg in sys.argv[1:]:
        if arg.startswith(("--enable-plugin=", "--plugin-enable=")):
            plugin_names = arg[16:]
            if "=" in plugin_names:
                logger.sysexit(
                    "Error, plugin options format changed. Use '--plugin-enable=%s --help' to know new options."
                    % plugin_names.split("=", 1)[0]
                )

            addPluginCommandLineOptions(
                parser=parser, plugin_names=plugin_names.split(",")
            )

        if arg.startswith("--user-plugin="):
            plugin_name = arg[14:]
            if "=" in plugin_name:
                logger.sysexit(
                    "Error, plugin options format changed. Use '--user-plugin=%s --help' to know new options."
                    % plugin_name
                )

            addUserPluginCommandLineOptions(parser=parser, filename=plugin_name)


def parseOptions(logger):
    # First, isolate the first non-option arguments.
    extra_args = []

    if is_nuitka_run:
        count = 0

        for count, arg in enumerate(sys.argv):
            if count == 0:
                continue

            if arg[0] != "-":
                break

            # Treat "--" as a terminator.
            if arg == "--":
                count += 1
                break

        if count > 0:
            extra_args = sys.argv[count + 1 :]
            sys.argv = sys.argv[0 : count + 1]

    # Next, lets activate plugins early, so they can inject more options to the parser.
    _considerPluginOptions(logger)

    options, positional_args = parser.parse_args()

    if options.list_plugins:
        from nuitka.plugins.Plugins import listPlugins

        listPlugins()
        sys.exit(0)

    if not positional_args:
        parser.print_help()

        logger.sysexit(
            """
Error, need positional argument with python module or main program."""
        )

    if not options.immediate_execution and len(positional_args) > 1:
        parser.print_help()

        logger.sysexit(
            """
Error, specify only one positional argument unless "--run" is specified to
pass them to the compiled program execution."""
        )

    return is_nuitka_run, options, positional_args, extra_args
