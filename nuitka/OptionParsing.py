#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Command line options of Nuitka.

These provide only the optparse options to use, and the mechanic to actually
do it, but updating and checking module "nuitka.Options" values is not in
the scope, to make sure it can be used without.

Note: This is using "optparse", because "argparse" is only Python 2.7 and
higher, and we still support Python 2.6 due to the RHELs still being used,
and despite the long deprecation, it's in every later release, and actually
pretty good.
"""

import os
import re
import sys
from string import Formatter

from nuitka.PythonFlavors import getPythonFlavorName
from nuitka.PythonVersions import isPythonWithGil
from nuitka.utils.CommandLineOptions import SUPPRESS_HELP, makeOptionsParser
from nuitka.utils.FileOperations import getFileContentByLine
from nuitka.utils.Utils import (
    getArchitecture,
    getLinuxDistribution,
    getOS,
    getWindowsRelease,
    isLinux,
    isMacOS,
    isWin32OrPosixWindows,
    isWin32Windows,
    withNoSyntaxWarning,
)
from nuitka.Version import getCommercialVersion, getNuitkaVersion

# Indicator if we were called as "nuitka-run" in which case we assume some
# other defaults and work a bit different with parameters.
_nuitka_binary_name = os.path.basename(sys.argv[0])
if _nuitka_binary_name == "__main__.py":
    _nuitka_binary_name = "%s -m nuitka" % os.path.basename(sys.executable)
is_nuitka_run = _nuitka_binary_name.lower().endswith("-run")

if not is_nuitka_run:
    usage_template = "usage: %s [--module] [--run] [options] main_module.py"
else:
    usage_template = "usage: %s [options] main_module.py"


parser = makeOptionsParser(usage=usage_template % _nuitka_binary_name)

parser.add_option(
    "--version",
    dest="version",
    action="store_true",
    default=False,
    require_compiling=False,
    help="""\
Show version information and important details for bug reports, then exit. Defaults to off.""",
)

parser.add_option(
    "--module",
    action="store_true",
    dest="module_mode",
    default=False,
    help="""\
Create an importable binary extension module executable instead of a program. Defaults to off.""",
)

parser.add_option(
    "--mode",
    action="store",
    dest="compilation_mode",
    metavar="COMPILATION_MODE",
    choices=("app", "onefile", "standalone", "accelerated", "module"),
    default=None,
    help="""\
Mode in which to compile. Accelerated runs in your Python
installation and depends on it. Standalone creates a folder
with an executable contained to run it. Onefile creates a
single executable to deploy. App is onefile except on macOS
where it's not to be used. Default is 'accelerated'.""",
)

parser.add_option(
    "--standalone",
    action="store_true",
    dest="is_standalone",
    default=False,
    help="""\
Enable standalone mode for output. This allows you to transfer the created binary
to other machines without it using an existing Python installation. This also
means it will become big. It implies these option: "--follow-imports" and
"--python-flag=no_site". Defaults to off.""",
)

parser.add_option(
    "--no-standalone",
    action="store_false",
    dest="is_standalone",
    default=False,
    help=SUPPRESS_HELP,
)


parser.add_option(
    "--onefile",
    action="store_true",
    dest="is_onefile",
    default=False,
    github_action_default=True,
    help="""\
On top of standalone mode, enable onefile mode. This means not a folder,
but a compressed executable is created and used. Defaults to off.""",
)

parser.add_option(
    "--no-onefile",
    action="store_false",
    dest="is_onefile",
    default=False,
    help=SUPPRESS_HELP,
)

parser.add_option(
    "--python-flag",
    action="append",
    dest="python_flags",
    metavar="FLAG",
    default=[],
    help="""\
Python flags to use. Default is what you are using to run Nuitka, this
enforces a specific mode. These are options that also exist to standard
Python executable. Currently supported: "-S" (alias "no_site"),
"static_hashes" (do not use hash randomization), "no_warnings" (do not
give Python run time warnings), "-O" (alias "no_asserts"), "no_docstrings"
(do not use doc strings), "-u" (alias "unbuffered"), "isolated" (do not
load outside code) and "-m" (package mode, compile as "package.__main__").
Default empty.""",
)

parser.add_option(
    "--python-debug",
    action="store_true",
    dest="python_debug",
    default=None,
    help="""\
Use debug version or not. Default uses what you are using to run Nuitka, most
likely a non-debug version. Only for debugging and testing purposes.""",
)

parser.add_option(
    "--python-for-scons",
    action="store",
    dest="python_scons",
    metavar="PATH",
    default=None,
    github_action=False,
    help="""\
When compiling with Python 3.4 provide the path of a
Python binary to use for Scons. Otherwise Nuitka can
use what you run Nuitka with, or find Python installation,
e.g. from Windows registry. On Windows, a Python 3.5 or
higher is needed. On non-Windows, a Python 2.6 or 2.7
will do as well.""",
)

parser.add_option(
    "--main",
    "--script-name",
    action="append",
    dest="mains",
    metavar="PATH",
    default=[],
    help="""\
If specified once, this takes the place of the
positional argument, i.e. the filename to compile.
When given multiple times, it enables "multidist"
(see User Manual) it allows you to create binaries
that depending on file name or invocation name.
""",
)

# Option for use with GitHub action workflow, where options are read
# from the environment variable with the input values given there.
parser.add_option(
    "--github-workflow-options",
    action="store_true",
    dest="github_workflow_options",
    default=False,
    github_action=False,
    help=SUPPRESS_HELP,  # For use in GitHub Action only.
)

include_group = parser.add_option_group(
    "Control the inclusion of modules and packages in result",
    link="include-section",
)

include_group.add_option(
    "--include-package",
    action="append",
    dest="include_packages",
    metavar="PACKAGE",
    default=[],
    help="""\
Include a whole package. Give as a Python namespace, e.g. "some_package.sub_package"
and Nuitka will then find it and include it and all the modules found below that
disk location in the binary or extension module it creates, and make it available
for import by the code. To avoid unwanted sub packages, e.g. tests you can e.g. do
this "--nofollow-import-to=*.tests". Default empty.""",
)

include_group.add_option(
    "--include-module",
    action="append",
    dest="include_modules",
    metavar="MODULE",
    default=[],
    help="""\
Include a single module. Give as a Python namespace, e.g. "some_package.some_module"
and Nuitka will then find it and include it in the binary or extension module
it creates, and make it available for import by the code. Default empty.""",
)

include_group.add_option(
    "--include-plugin-directory",
    action="append",
    dest="include_extra",
    metavar="MODULE/PACKAGE",
    default=[],
    help="""\
Include also the code found in that directory, considering as if
they are each given as a main file. Overrides all other inclusion
options. You ought to prefer other inclusion options, that go by
names, rather than filenames, those find things through being in
"sys.path". This option is for very special use cases only. Can
be given multiple times. Default empty.""",
)

include_group.add_option(
    "--include-plugin-files",
    action="append",
    dest="include_extra_files",
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

del include_group


follow_group = parser.add_option_group("Control the following into imported modules")

follow_group.add_option(
    "--follow-imports",
    action="store_true",
    dest="follow_all",
    default=None,
    help="""\
Descend into all imported modules. Defaults to on in standalone mode, otherwise off.""",
)

follow_group.add_option(
    "--follow-import-to",
    action="append",
    dest="follow_modules",
    metavar="MODULE/PACKAGE",
    default=[],
    help="""\
Follow to that module if used, or if a package, to the whole package. Can be given
multiple times. Default empty.""",
)

follow_group.add_option(
    "--nofollow-import-to",
    action="append",
    dest="follow_not_modules",
    metavar="MODULE/PACKAGE",
    default=[],
    help="""\
Do not follow to that module name even if used, or if a package name, to the
whole package in any case, overrides all other options. This can also contain
patterns, e.g. "*.tests". Can be given multiple times. Default empty.""",
)

follow_group.add_option(
    "--nofollow-imports",
    action="store_false",
    dest="follow_all",
    default=None,
    help="""\
Do not descend into any imported modules at all, overrides all other inclusion
options and not usable for standalone mode. Defaults to off.""",
)

follow_group.add_option(
    "--follow-stdlib",
    action="store_true",
    dest="follow_stdlib",
    default=False,
    help="""\
Also descend into imported modules from standard library. This will increase
the compilation time by a lot and is also not well tested at this time and
sometimes won't work. Defaults to off.""",
)

del follow_group

onefile_group = parser.add_option_group("Onefile options")

onefile_group.add_option(
    "--onefile-tempdir-spec",
    action="store",
    dest="onefile_tempdir_spec",
    metavar="ONEFILE_TEMPDIR_SPEC",
    default=None,
    help="""\
Use this as a folder to unpack to in onefile mode. Defaults to
'{TEMP}/onefile_{PID}_{TIME}', i.e. user temporary directory
and being non-static it's removed. Use e.g. a string like
'{CACHE_DIR}/{COMPANY}/{PRODUCT}/{VERSION}' which is a good
static cache path, this will then not be removed.""",
)

onefile_group.add_option(
    "--onefile-child-grace-time",
    action="store",
    dest="onefile_child_grace_time",
    metavar="GRACE_TIME_MS",
    default=None,
    help="""\
When stopping the child, e.g. due to CTRL-C or shutdown, etc. the
Python code gets a "KeyboardInterrupt", that it may handle e.g. to
flush data. This is the amount of time in ms, before the child it
killed in the hard way. Unit is ms, and default 5000.""",
)

onefile_group.add_option(
    "--onefile-no-compression",
    action="store_true",
    dest="onefile_no_compression",
    default=False,
    help="""\
When creating the onefile, disable compression of the payload. This is
mostly for debug purposes, or to save time. Default is off.""",
)

onefile_group.add_option(
    "--onefile-as-archive",
    action="store_true",
    dest="onefile_as_archive",
    default=False,
    help="""\
When creating the onefile, use an archive format, that can be unpacked
with "nuitka-onefile-unpack" rather than a stream that only the onefile
program itself unpacks. Default is off.""",
)

del onefile_group

data_group = parser.add_option_group("Data files")

data_group.add_option(
    "--include-package-data",
    action="append",
    dest="package_data",
    metavar="PACKAGE",
    default=[],
    help="""\
Include data files for the given package name. DLLs and extension modules
are not data files and never included like this. Can use patterns the
filenames as indicated below. Data files of packages are not included
by default, but package configuration can do it.
This will only include non-DLL, non-extension modules, i.e. actual data
files. After a ":" optionally a filename pattern can be given as
well, selecting only matching files. Examples:
"--include-package-data=package_name" (all files)
"--include-package-data=package_name:*.txt" (only certain type)
"--include-package-data=package_name:some_filename.dat (concrete file)
Default empty.""",
)

data_group.add_option(
    "--include-data-files",
    action="append",
    dest="data_files",
    metavar="DESC",
    default=[],
    help="""\
Include data files by filenames in the distribution. There are many
allowed forms. With '--include-data-files=/path/to/file/*.txt=folder_name/some.txt' it
will copy a single file and complain if it's multiple. With
'--include-data-files=/path/to/files/*.txt=folder_name/' it will put
all matching files into that folder. For recursive copy there is a
form with 3 values that '--include-data-files=/path/to/scan=folder_name/=**/*.txt'
that will preserve directory structure. Default empty.""",
)

data_group.add_option(
    "--include-data-dir",
    action="append",
    dest="data_dirs",
    metavar="DIRECTORY",
    default=[],
    help="""\
Include data files from complete directory in the distribution. This is
recursive. Check '--include-data-files' with patterns if you want non-recursive
inclusion. An example would be '--include-data-dir=/path/some_dir=data/some_dir'
for plain copy, of the whole directory. All non-code files are copied, if you
want to use '--noinclude-data-files' option to remove them. Default empty.""",
)

data_group.add_option(
    "--noinclude-data-files",
    action="append",
    dest="data_files_inhibited",
    metavar="PATTERN",
    default=[],
    help="""\
Do not include data files matching the filename pattern given. This is against
the target filename, not source paths. So to ignore a file pattern from package
data for 'package_name' should be matched as 'package_name/*.txt'. Or for the
whole directory simply use 'package_name'. Default empty.""",
)

data_group.add_option(
    "--include-onefile-external-data",
    action="append",
    dest="data_files_external",
    metavar="PATTERN",
    default=[],
    help="""\
Include the specified data file patterns outside of the onefile binary,
rather than on the inside. Makes only sense in case of '--onefile'
compilation. First files have to be specified as included with other
`--include-*data*` options, and then this refers to target paths
inside the distribution. Default empty.""",
)

data_group.add_option(
    "--list-package-data",
    action="store",
    dest="list_package_data",
    default="",
    require_compiling=False,
    help="""\
Output the data files found for a given package name. Default not done.""",
)

data_group.add_option(
    "--include-raw-dir",
    action="append",
    dest="raw_dirs",
    metavar="DIRECTORY",
    default=[],
    help="""\
Include raw directories completely in the distribution. This is
recursive. Check '--include-data-dir' to use the sane option.
Default empty.""",
)


del data_group

metadata_group = parser.add_option_group("Metadata support")

metadata_group.add_option(
    "--include-distribution-metadata",
    action="append",
    dest="include_distribution_metadata",
    metavar="DISTRIBUTION",
    default=[],
    help="""\
Include metadata information for the given distribution name. Some packages
check metadata for presence, version, entry points, etc. and without this
option given, it only works when it's recognized at compile time which is
not always happening. This of course only makes sense for packages that are
included in the compilation. Default empty.""",
)

del metadata_group

dll_group = parser.add_option_group("DLL files")

dll_group.add_option(
    "--noinclude-dlls",
    action="append",
    dest="dll_files_inhibited",
    metavar="PATTERN",
    default=[],
    help="""\
Do not include DLL files matching the filename pattern given. This is against
the target filename, not source paths. So ignore a DLL 'someDLL' contained in
the package 'package_name' it should be matched as 'package_name/someDLL.*'.
Default empty.""",
)


dll_group.add_option(
    "--list-package-dlls",
    action="store",
    dest="list_package_dlls",
    default="",
    require_compiling=False,
    help="""\
Output the DLLs found for a given package name. Default not done.""",
)

del dll_group

warnings_group = parser.add_option_group("Control the warnings to be given by Nuitka")


warnings_group.add_option(
    "--warn-implicit-exceptions",
    action="store_true",
    dest="warn_implicit_exceptions",
    default=False,
    help="""\
Enable warnings for implicit exceptions detected at compile time.""",
)

warnings_group.add_option(
    "--warn-unusual-code",
    action="store_true",
    dest="warn_unusual_code",
    default=False,
    help="""\
Enable warnings for unusual code detected at compile time.""",
)

warnings_group.add_option(
    "--assume-yes-for-downloads",
    action="store_true",
    dest="assume_yes_for_downloads",
    default=False,
    github_action_default=True,
    help="""\
Allow Nuitka to download external code if necessary, e.g. dependency
walker, ccache, and even gcc on Windows. To disable, redirect input
from nul device, e.g. "</dev/null" or "<NUL:". Default is to prompt.""",
)


warnings_group.add_option(
    "--nowarn-mnemonic",
    action="append",
    dest="nowarn_mnemonics",
    metavar="MNEMONIC",
    default=[],
    help="""\
Disable warning for a given mnemonic. These are given to make sure you are aware of
certain topics, and typically point to the Nuitka website. The mnemonic is the part
of the URL at the end, without the HTML suffix. Can be given multiple times and
accepts shell pattern. Default empty.""",
)

del warnings_group


execute_group = parser.add_option_group("Immediate execution after compilation")

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
Execute inside a debugger, e.g. "gdb" or "lldb" to automatically get a stack trace.
Defaults to off.""",
)

del execute_group


compilation_group = parser.add_option_group("Compilation choices")

compilation_group.add_option(
    "--user-package-configuration-file",
    action="append",
    dest="user_yaml_files",
    default=[],
    metavar="YAML_FILENAME",
    help="""\
User provided Yaml file with package configuration. You can include DLLs,
remove bloat, add hidden dependencies. Check the Nuitka Package Configuration
Manual for a complete description of the format to use. Can be given
multiple times. Defaults to empty.""",
)

compilation_group.add_option(
    "--full-compat",
    action="store_false",
    dest="improved",
    default=True,
    help="""\
Enforce absolute compatibility with CPython. Do not even allow minor
deviations from CPython behavior, e.g. not having better tracebacks
or exception messages which are not really incompatible, but only
different or worse. This is intended for tests only and should *not*
be used.""",
)

compilation_group.add_option(
    "--file-reference-choice",
    action="store",
    dest="file_reference_mode",
    metavar="FILE_MODE",
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

compilation_group.add_option(
    "--module-name-choice",
    action="store",
    dest="module_name_mode",
    metavar="MODULE_NAME_MODE",
    choices=("original", "runtime"),
    default=None,
    help="""\
Select what value "__name__" and "__package__" are going to be. With "runtime"
(default for module mode), the created module uses the parent package to
deduce the value of "__package__", to be fully compatible. The value "original"
(default for other modes) allows for more static optimization to happen, but
is incompatible for modules that normally can be loaded into any package.""",
)


del compilation_group

output_group = parser.add_option_group("Output choices")

output_group.add_option(
    "--output-filename",
    "-o",
    action="store",
    dest="output_filename",
    metavar="FILENAME",
    default=None,
    help="""\
Specify how the executable should be named. For extension modules there is no
choice, also not for standalone mode and using it will be an error. This may
include path information that needs to exist though. Defaults to '%s' on this
platform.
"""
    % ("<program_name>" + (".exe" if isWin32OrPosixWindows() else ".bin")),
)

output_group.add_option(
    "--output-dir",
    action="store",
    dest="output_dir",
    metavar="DIRECTORY",
    default="",
    help="""\
Specify where intermediate and final output files should be put. The DIRECTORY
will be populated with build folder, dist folder, binaries, etc.
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
Do not create a '.pyi' file for extension modules created by Nuitka. This is
used to detect implicit imports.
Defaults to off.""",
)

output_group.add_option(
    "--no-pyi-stubs",
    action="store_false",
    dest="pyi_stubs",
    default=True,
    help="""\
Do not use stubgen when creating a '.pyi' file for extension modules
created by Nuitka. They expose your API, but stubgen may cause issues.
Defaults to off.""",
)


del output_group

deployment_group = parser.add_option_group("Deployment control")

deployment_group.add_option(
    "--deployment",
    action="store_true",
    dest="is_deployment",
    default=False,
    help="""\
Disable code aimed at making finding compatibility issues easier. This
will e.g. prevent execution with "-c" argument, which is often used by
code that attempts run a module, and causes a program to start itself
over and over potentially. Disable once you deploy to end users, for
finding typical issues, this is very helpful during development. Default
off.""",
)

deployment_group.add_option(
    "--no-deployment-flag",
    action="append",
    dest="no_deployment_flags",
    metavar="FLAG",
    default=[],
    help="""\
Keep deployment mode, but disable selectively parts of it. Errors from
deployment mode will output these identifiers. Default empty.""",
)

environment_group = parser.add_option_group("Environment control")

environment_group.add_option(
    "--force-runtime-environment-variable",
    action="append",
    dest="forced_runtime_env_variables",
    metavar="VARIABLE_SPEC",
    default=[],
    help="""\
Force an environment variables to a given value. Default empty.""",
)

del environment_group

debug_group = parser.add_option_group("Debug features")

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
    "--no-debug-immortal-assumptions",
    action="store_false",
    dest="debug_immortal",
    default=None,
    help="""\
Disable check normally done with "--debug". With Python3.12+ do not check known
immortal object assumptions. Some C libraries corrupt them. Defaults to check
being made if "--debug" is on.""",
)

debug_group.add_option(
    "--debug-immortal-assumptions",
    action="store_true",
    dest="debug_immortal",
    default=None,
    help=SUPPRESS_HELP,
)

debug_group.add_option(
    "--unstripped",
    "--unstriped",
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
    github_action=False,
    help="""\
Enable vmprof based profiling of time spent. Not working currently. Defaults to off.""",
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
    "--xml",
    action="store",
    dest="xml_output",
    metavar="XML_FILENAME",
    default=None,
    help="Write the internal program structure, result of optimization in XML form to given filename.",
)

debug_group.add_option(
    "--experimental",
    action="append",
    dest="experimental",
    metavar="FLAG",
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

debug_group.add_option(
    "--low-memory",
    action="store_true",
    dest="low_memory",
    default=False,
    help="""\
Attempt to use less memory, by forking less C compilation jobs and using
options that use less memory. For use on embedded machines. Use this in
case of out of memory problems. Defaults to off.""",
)

debug_group.add_option(
    "--create-environment-from-report",
    action="store",
    dest="create_environment_from_report",
    default="",
    require_compiling=False,
    help="""\
Create a new virtualenv in that non-existing path from the report file given with
e.g. '--report=compilation-report.xml'. Default not done.""",
)

debug_group.add_option(
    "--generate-c-only",
    action="store_true",
    dest="generate_c_only",
    default=False,
    github_action=False,
    help="""\
Generate only C source code, and do not compile it to binary or module. This
is for debugging and code coverage analysis that doesn't waste CPU. Defaults to
off. Do not think you can use this directly.""",
)


del debug_group


development_group = parser.add_option_group("Nuitka Development features")


development_group.add_option(
    "--devel-missing-code-helpers",
    action="store_true",
    dest="report_missing_code_helpers",
    default=False,
    help="""\
Report warnings for code helpers for types that were attempted, but don't
exist. This helps to identify opportunities for improving optimization of
generated code from type knowledge not used. Default False.""",
)

development_group.add_option(
    "--devel-missing-trust",
    action="store_true",
    dest="report_missing_trust",
    default=False,
    help="""\
Report warnings for imports that could be trusted, but currently are not. This
is to identify opportunities for improving handling of hard modules, where this
sometimes could allow more static optimization. Default False.""",
)

development_group.add_option(
    "--devel-recompile-c-only",
    action="store_true",
    dest="recompile_c_only",
    default=False,
    github_action=False,
    help="""\
This is not incremental compilation, but for Nuitka development only. Takes
existing files and simply compiles them as C again after doing the Python
steps. Allows compiling edited C files for manual debugging changes to the
generated source. Allows us to add printing, check and print values, but it
is now what users would want. Depends on compiling Python source to
determine which files it should look at.""",
)

development_group.add_option(
    "--devel-internal-graph",
    action="store_true",
    dest="internal_graph",
    default=False,
    github_action=False,
    help="""\
Create graph of optimization process internals, do not use for whole programs, but only
for small test cases. Defaults to off.""",
)


del development_group

# This is for testing framework, "coverage.py" hates to loose the process. And
# we can use it to make sure it's not done unknowingly.
parser.add_option(
    "--must-not-re-execute",
    action="store_false",
    dest="allow_reexecute",
    default=True,
    github_action=False,
    help=SUPPRESS_HELP,
)

# Not sure where to put this yet, intended to helps me edit code faster, will
# make it public if it becomes useful.
parser.add_option(
    "--edit-module-code",
    action="store",
    dest="edit_module_code",
    default=None,
    require_compiling=False,
    help=SUPPRESS_HELP,
)


c_compiler_group = parser.add_option_group("Backend C compiler choice")

c_compiler_group.add_option(
    "--clang",
    action="store_true",
    dest="clang",
    default=False,
    help="""\
Enforce the use of clang. On Windows this requires a working Visual
Studio version to piggy back on. Defaults to off.""",
)

c_compiler_group.add_option(
    "--mingw64",
    action="store_true",
    dest="mingw64",
    default=False,
    help="""\
Enforce the use of MinGW64 on Windows. Defaults to off unless MSYS2 with MinGW Python is used.""",
)

c_compiler_group.add_option(
    "--msvc",
    action="store",
    dest="msvc_version",
    default=None,
    help="""\
Enforce the use of specific MSVC version on Windows. Allowed values
are e.g. "14.3" (MSVC 2022) and other MSVC version numbers, specify
"list" for a list of installed compilers, or use "latest".

Defaults to latest MSVC being used if installed, otherwise MinGW64
is used.""",
)

c_compiler_group.add_option(
    "--jobs",
    "-j",
    action="store",
    dest="jobs",
    metavar="N",
    default=None,
    help="""\
Specify the allowed number of parallel C compiler jobs. Negative values
are system CPU minus the given value. Defaults to the full system CPU
count unless low memory mode is activated, then it defaults to 1.""",
)

c_compiler_group.add_option(
    "--lto",
    action="store",
    dest="lto",
    metavar="choice",
    default="auto",
    choices=("yes", "no", "auto"),
    help="""\
Use link time optimizations (MSVC, gcc, clang). Allowed values are
"yes", "no", and "auto" (when it's known to work). Defaults to
"auto".""",
)

c_compiler_group.add_option(
    "--static-libpython",
    action="store",
    dest="static_libpython",
    metavar="choice",
    default="auto",
    choices=("yes", "no", "auto"),
    help="""\
Use static link library of Python. Allowed values are "yes", "no",
and "auto" (when it's known to work). Defaults to "auto".""",
)

c_compiler_group.add_option(
    "--cf-protection",
    action="store",
    dest="cf_protection",
    metavar="PROTECTION_MODE",
    default="auto",
    choices=("auto", "full", "branch", "return", "none", "check"),
    help="""\
This option is gcc specific. For the gcc compiler, select the
"cf-protection" mode. Default "auto" is to use the gcc default
value, but you can override it, e.g. to disable it with "none"
value. Refer to gcc documentation for "-fcf-protection" for the
details.""",
)

del c_compiler_group

caching_group = parser.add_option_group("Cache Control")

_cache_names = ("all", "ccache", "bytecode", "compression")

if isWin32Windows():
    _cache_names += ("dll-dependencies",)

caching_group.add_option(
    "--disable-cache",
    action="append",
    dest="disabled_caches",
    choices=_cache_names,
    default=[],
    help="""\
Disable selected caches, specify "all" for all cached. Currently allowed
values are: %s. can be given multiple times or with comma separated values.
Default none."""
    % (",".join('"%s"' % cache_name for cache_name in _cache_names)),
)

caching_group.add_option(
    "--clean-cache",
    action="append",
    dest="clean_caches",
    choices=_cache_names,
    default=[],
    require_compiling=False,
    help="""\
Clean the given caches before executing, specify "all" for all cached. Currently
allowed values are: %s. can be given multiple times or with comma separated
values. Default none."""
    % (",".join('"%s"' % cache_name for cache_name in _cache_names)),
)

caching_group.add_option(
    "--disable-bytecode-cache",
    action="store_true",
    dest="disable_bytecode_cache",
    default=False,
    help=SUPPRESS_HELP,
)

caching_group.add_option(
    "--disable-ccache",
    action="store_true",
    dest="disable_ccache",
    default=False,
    help=SUPPRESS_HELP,
)

caching_group.add_option(
    "--disable-dll-dependency-cache",
    action="store_true",
    dest="disable_dll_dependency_cache",
    default=False,
    help=SUPPRESS_HELP,
)

if isWin32Windows():
    caching_group.add_option(
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


del caching_group

pgo_group = parser.add_option_group("PGO compilation choices")

pgo_group.add_option(
    "--pgo-c",
    action="store_true",
    dest="is_c_pgo",
    default=False,
    help="""\
Enables C level profile guided optimization (PGO), by executing a dedicated build first
for a profiling run, and then using the result to feedback into the C compilation.
Note: This is experimental and not working with standalone modes of Nuitka yet.
Defaults to off.""",
)

pgo_group.add_option(
    "--pgo-python",
    action="store_true",
    dest="is_python_pgo",
    default=False,
    help=SUPPRESS_HELP,  # Not yet ready
)

pgo_group.add_option(
    "--pgo-python-input",
    action="store",
    dest="python_pgo_input",
    default=None,
    help=SUPPRESS_HELP,  # Not yet ready
)

pgo_group.add_option(
    "--pgo-python-policy-unused-module",
    action="store",
    dest="python_pgo_policy_unused_module",
    choices=("include", "exclude", "bytecode"),
    default="include",
    help=SUPPRESS_HELP,  # Not yet ready
)

pgo_group.add_option(
    "--pgo-args",
    action="store",
    dest="pgo_args",
    default="",
    help="""\
Arguments to be passed in case of profile guided optimization. These are passed to the special
built executable during the PGO profiling run. Default empty.""",
)

pgo_group.add_option(
    "--pgo-executable",
    action="store",
    dest="pgo_executable",
    default=None,
    help="""\
Command to execute when collecting profile information. Use this only, if you need to
launch it through a script that prepares it to run. Default use created program.""",
)


del pgo_group


tracing_group = parser.add_option_group("Tracing features")

tracing_group.add_option(
    "--report",
    action="store",
    dest="compilation_report_filename",
    metavar="REPORT_FILENAME",
    default=None,
    help="""\
Report module, data files, compilation, plugin, etc. details in an XML output file. This
is also super useful for issue reporting. These reports can e.g. be used to re-create
the environment easily using it with '--create-environment-from-report', but contain a
lot of information. Default is off.""",
)

tracing_group.add_option(
    "--report-diffable",
    action="store_true",
    dest="compilation_report_diffable",
    metavar="REPORT_DIFFABLE",
    default=False,
    help="""\
Report data in diffable form, i.e. no timing or memory usage values that vary from run
to run. Default is off.""",
)

tracing_group.add_option(
    "--report-user-provided",
    action="append",
    dest="compilation_report_user_data",
    metavar="KEY_VALUE",
    default=[],
    help="""\
Report data from you. This can be given multiple times and be
anything in 'key=value' form, where key should be an identifier, e.g. use
'--report-user-provided=pipenv-lock-hash=64a5e4' to track some input values.
Default is empty.""",
)


tracing_group.add_option(
    "--report-template",
    action="append",
    dest="compilation_report_templates",
    metavar="REPORT_DESC",
    default=[],
    help="""\
Report via template. Provide template and output filename 'template.rst.j2:output.rst'. For
built-in templates, check the User Manual for what these are. Can be given multiple times.
Default is empty.""",
)


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
Run the C building backend Scons with verbose information, showing the executed commands,
detected compilers. Defaults to off.""",
)

tracing_group.add_option(
    "--no-progressbar",
    "--no-progress-bar",
    action="store_false",
    dest="progress_bar",
    default=True,
    github_action=False,
    help="""Disable progress bars. Defaults to off.""",
)

tracing_group.add_option(
    "--show-progress",
    action="store_true",
    dest="show_progress",
    default=False,
    github_action=False,
    help="""Obsolete: Provide progress information and statistics.
Disables normal progress bar. Defaults to off.""",
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
    github_action=False,
    help="""\
Provide information for included modules and DLLs
Obsolete: You should use '--report' file instead. Defaults to off.""",
)

tracing_group.add_option(
    "--show-modules-output",
    action="store",
    dest="show_inclusion_output",
    metavar="PATH",
    default=None,
    github_action=False,
    help="""\
Where to output '--show-modules', should be a filename. Default is standard output.""",
)

tracing_group.add_option(
    "--verbose",
    action="store_true",
    dest="verbose",
    default=False,
    github_action=False,
    help="""\
Output details of actions taken, esp. in optimizations. Can become a lot.
Defaults to off.""",
)

tracing_group.add_option(
    "--verbose-output",
    action="store",
    dest="verbose_output",
    metavar="PATH",
    default=None,
    github_action=False,
    help="""\
Where to output from '--verbose', should be a filename. Default is standard output.""",
)

del tracing_group


os_group = parser.add_option_group("General OS controls")

os_group.add_option(
    "--force-stdout-spec",
    "--windows-force-stdout-spec",
    action="store",
    dest="force_stdout_spec",
    metavar="FORCE_STDOUT_SPEC",
    default=None,
    help="""\
Force standard output of the program to go to this location. Useful for programs with
disabled console and programs using the Windows Services Plugin of Nuitka commercial.
Defaults to not active, use e.g. '{PROGRAM_BASE}.out.txt', i.e. file near your program,
check User Manual for full list of available values.""",
)

os_group.add_option(
    "--force-stderr-spec",
    "--windows-force-stderr-spec",
    action="store",
    dest="force_stderr_spec",
    metavar="FORCE_STDERR_SPEC",
    default=None,
    help="""\
Force standard error of the program to go to this location. Useful for programs with
disabled console and programs using the Windows Services Plugin of Nuitka commercial.
Defaults to not active, use e.g. '{PROGRAM_BASE}.err.txt', i.e. file near your program,
check User Manual for full list of available values.""",
)

del os_group


windows_group = parser.add_option_group("Windows specific controls")

windows_group.add_option(
    "--windows-console-mode",
    action="store",
    dest="console_mode",
    choices=("force", "disable", "attach", "hide"),
    metavar="CONSOLE_MODE",
    default=None,
    help="""\
Select console mode to use. Default mode is 'force' and creates a
console window unless the program was started from one. With 'disable'
it doesn't create or use a console at all. With 'attach' an existing
console will be used for outputs. With 'hide' a newly spawned console
will be hidden and an already existing console will behave like
'force'. Default is 'force'.
""",
)

windows_group.add_option(
    "--windows-icon-from-ico",
    action="append",
    dest="windows_icon_path",
    metavar="ICON_PATH",
    default=[],
    help="""\
Add executable icon. Can be given multiple times for different resolutions
or files with multiple icons inside. In the later case, you may also suffix
with #<n> where n is an integer index starting from 1, specifying a specific
icon to be included, and all others to be ignored.""",
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
    "--onefile-windows-splash-screen-image",
    action="store",
    dest="splash_screen_image",
    default=None,
    help="""\
When compiling for Windows and onefile, show this while loading the application. Defaults to off.""",
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
    "--windows-uac-uiaccess",  # spell-checker: ignore uiaccess
    action="store_true",
    dest="windows_uac_uiaccess",
    metavar="WINDOWS_UAC_UIACCESS",
    default=False,
    help="""\
Request Windows User Control, to enforce running from a few folders only, remote
desktop access. (Windows only). Defaults to off.""",
)

windows_group.add_option(
    "--disable-console",
    "--macos-disable-console",
    "--windows-disable-console",
    action="store_true",
    dest="disable_console",
    default=None,
    help=SUPPRESS_HELP,
)

windows_group.add_option(
    "--enable-console",
    action="store_false",
    dest="disable_console",
    default=None,
    help=SUPPRESS_HELP,
)

windows_group.add_option(
    "--windows-dependency-tool",
    action="store",
    dest="dependency_tool",
    default=None,
    help=SUPPRESS_HELP,
)


del windows_group


macos_group = parser.add_option_group("macOS specific controls")

macos_group.add_option(
    "--macos-create-app-bundle",
    action="store_true",
    dest="macos_create_bundle",
    default=False,
    help="""\
When compiling for macOS, create a bundle rather than a plain binary
application. This is the only way to unlock the disabling of console,
get high DPI graphics, etc. and implies standalone mode. Defaults to
off.""",
)

macos_group.add_option(
    "--macos-target-arch",
    action="store",
    dest="macos_target_arch",
    choices=("universal", "arm64", "x86_64"),
    metavar="MACOS_TARGET_ARCH",
    default=None,
    help="""\
What architectures is this to supposed to run on. Default and limit
is what the running Python allows for. Default is "native" which is
the architecture the Python is run with.""",
)

macos_group.add_option(
    "--macos-app-icon",
    action="append",
    dest="macos_icon_path",
    metavar="ICON_PATH",
    default=[],
    help="Add icon for the application bundle to use. Can be given only one time. Defaults to Python icon if available.",
)


macos_group.add_option(
    "--macos-signed-app-name",
    action="store",
    dest="macos_signed_app_name",
    metavar="MACOS_SIGNED_APP_NAME",
    default=None,
    help="""\
Name of the application to use for macOS signing. Follow "com.YourCompany.AppName"
naming results for best results, as these have to be globally unique, and will
potentially grant protected API accesses.""",
)

macos_group.add_option(
    "--macos-app-name",
    action="store",
    dest="macos_app_name",
    metavar="MACOS_APP_NAME",
    default=None,
    help="""\
Name of the product to use in macOS bundle information. Defaults to base
filename of the binary.""",
)

macos_group.add_option(
    "--macos-app-mode",
    action="store",
    dest="macos_app_mode",
    metavar="APP_MODE",
    choices=("gui", "background", "ui-element"),
    default="gui",
    help="""\
Mode of application for the application bundle. When launching a Window, and appearing
in Docker is desired, default value "gui" is a good fit. Without a Window ever, the
application is a "background" application. For UI elements that get to display later,
"ui-element" is in-between. The application will not appear in dock, but get full
access to desktop when it does open a Window later.""",
)

macos_group.add_option(
    "--macos-sign-identity",
    action="store",
    dest="macos_sign_identity",
    metavar="MACOS_APP_VERSION",
    default="ad-hoc",
    help="""\
When signing on macOS, by default an ad-hoc identify will be used, but with this
option your get to specify another identity to use. The signing of code is now
mandatory on macOS and cannot be disabled. Use "auto" to detect your only identity
installed. Default "ad-hoc" if not given.""",
)

macos_group.add_option(
    "--macos-sign-notarization",
    action="store_true",
    dest="macos_sign_notarization",
    default=False,
    help="""\
When signing for notarization, using a proper TeamID identity from Apple, use
the required runtime signing option, such that it can be accepted.""",
)


macos_group.add_option(
    "--macos-app-version",
    action="store",
    dest="macos_app_version",
    metavar="MACOS_APP_VERSION",
    default=None,
    help="""\
Product version to use in macOS bundle information. Defaults to "1.0" if
not given.""",
)

macos_group.add_option(
    "--macos-app-protected-resource",
    action="append",
    dest="macos_protected_resources",
    metavar="RESOURCE_DESC",
    default=[],
    help="""\
Request an entitlement for access to a macOS protected resources, e.g.
"NSMicrophoneUsageDescription:Microphone access for recording audio."
requests access to the microphone and provides an informative text for
the user, why that is needed. Before the colon, is an OS identifier for
an access right, then the informative text. Legal values can be found on
https://developer.apple.com/documentation/bundleresources/information_property_list/protected_resources and
the option can be specified multiple times. Default empty.""",
)


del macos_group


linux_group = parser.add_option_group("Linux specific controls")

linux_group.add_option(
    "--linux-icon",
    "--linux-onefile-icon",
    action="append",
    dest="linux_icon_path",
    metavar="ICON_PATH",
    default=[],
    help="Add executable icon for onefile binary to use. Can be given only one time. Defaults to Python icon if available.",
)

del linux_group

version_group = parser.add_option_group("Binary Version Information")

version_group.add_option(
    "--company-name",
    "--windows-company-name",
    action="store",
    dest="company_name",
    metavar="COMPANY_NAME",
    default=None,
    help="Name of the company to use in version information. Defaults to unused.",
)

version_group.add_option(
    "--product-name",
    "--windows-product-name",
    action="store",
    dest="product_name",
    metavar="PRODUCT_NAME",
    default=None,
    help="""\
Name of the product to use in version information. Defaults to base filename of the binary.""",
)

version_group.add_option(
    "--file-version",
    "--windows-file-version",
    action="store",
    dest="file_version",
    metavar="FILE_VERSION",
    default=None,
    help="""\
File version to use in version information. Must be a sequence of up to 4
numbers, e.g. 1.0 or 1.0.0.0, no more digits are allowed, no strings are
allowed. Defaults to unused.""",
)

version_group.add_option(
    "--product-version",
    "--windows-product-version",
    action="store",
    dest="product_version",
    metavar="PRODUCT_VERSION",
    default=None,
    help="""\
Product version to use in version information. Same rules as for file version.
Defaults to unused.""",
)

version_group.add_option(
    "--file-description",
    "--windows-file-description",
    action="store",
    dest="file_description",
    metavar="FILE_DESCRIPTION",
    default=None,
    help="""\
Description of the file used in version information. Windows only at this time. Defaults to binary filename.""",
)

version_group.add_option(
    "--copyright",
    action="store",
    dest="legal_copyright",
    metavar="COPYRIGHT_TEXT",
    default=None,
    help="""\
Copyright used in version information. Windows/macOS only at this time. Defaults to not present.""",
)

version_group.add_option(
    "--trademarks",
    action="store",
    dest="legal_trademarks",
    metavar="TRADEMARK_TEXT",
    default=None,
    help="""\
Trademark used in version information. Windows/macOS only at this time. Defaults to not present.""",
)


del version_group

plugin_group = parser.add_option_group("Plugin control")

plugin_group.add_option(
    "--enable-plugins",
    "--plugin-enable",
    action="append",
    dest="plugins_enabled",
    metavar="PLUGIN_NAME",
    default=[],
    help="""\
Enabled plugins. Must be plug-in names. Use '--plugin-list' to query the
full list and exit. Default empty.""",
)

plugin_group.add_option(
    "--disable-plugins",
    "--plugin-disable",
    action="append",
    dest="plugins_disabled",
    metavar="PLUGIN_NAME",
    default=[],
    github_action=False,
    help="""\
Disabled plugins. Must be plug-in names. Use '--plugin-list' to query the
full list and exit. Most standard plugins are not a good idea to disable.
Default empty.""",
)

plugin_group.add_option(
    "--user-plugin",
    action="append",
    dest="user_plugins",
    metavar="PATH",
    default=[],
    help="The file name of user plugin. Can be given multiple times. Default empty.",
)

plugin_group.add_option(
    "--plugin-list",
    action="store_true",
    dest="plugin_list",
    default=False,
    require_compiling=False,
    github_action=False,
    help="""\
Show list of all available plugins and exit. Defaults to off.""",
)

plugin_group.add_option(
    "--plugin-no-detection",
    action="store_false",
    dest="detect_missing_plugins",
    default=True,
    help="""\
Plugins can detect if they might be used, and the you can disable the warning
via "--disable-plugin=plugin-that-warned", or you can use this option to disable
the mechanism entirely, which also speeds up compilation slightly of course as
this detection code is run in vain once you are certain of which plugins to
use. Defaults to off.""",
)

plugin_group.add_option(
    "--module-parameter",
    action="append",
    dest="module_parameters",
    default=[],
    help="""\
Provide a module parameter. You are asked by some packages
to provide extra decisions. Format is currently
--module-parameter=module.name-option-name=value
Default empty.""",
)

plugin_group.add_option(
    "--show-source-changes",
    action="append",
    dest="show_source_changes",
    default=[],
    github_action=False,
    help="""\
Show source changes to original Python file content before compilation. Mostly
intended for developing plugins and Nuitka package configuration. Use e.g.
'--show-source-changes=numpy.**' to see all changes below a given namespace
or use '*' to see everything which can get a lot.
Default empty.""",
)

del plugin_group

target_group = parser.add_option_group("Cross compilation")


target_group.add_option(
    "--target",
    action="store",
    dest="target_desc",
    metavar="TARGET_DESC",
    default=None,
    help="""\
Cross compilation target. Highly experimental and in development, not
supposed to work yet. We are working on '--target=wasi' and nothing
else yet.""",
)

del target_group


def _considerPluginOptions(logger):
    # Cyclic dependency on plugins during parsing of command line.
    from nuitka.plugins.Plugins import (
        addPluginCommandLineOptions,
        addStandardPluginCommandLineOptions,
        addUserPluginCommandLineOptions,
    )

    addStandardPluginCommandLineOptions(parser=parser)

    for arg in sys.argv[1:]:
        if arg.startswith(
            ("--enable-plugin=", "--enable-plugins=", "--plugin-enable=")
        ):
            plugin_names = arg.split("=", 1)[1]
            if "=" in plugin_names:
                logger.sysexit(
                    "Error, plugin options format changed. Use '--enable-plugin=%s --help' to know new options."
                    % plugin_names.split("=", 1)[0]
                )

            addPluginCommandLineOptions(
                parser=parser,
                plugin_names=plugin_names.split(","),
            )

        if arg.startswith("--user-plugin="):
            plugin_name = arg[14:]
            if "=" in plugin_name:
                logger.sysexit(
                    "Error, plugin options format changed. Use '--user-plugin=%s --help' to know new options."
                    % plugin_name.split("=", 1)[0]
                )

            addUserPluginCommandLineOptions(parser=parser, filename=plugin_name)


run_time_variable_names = (
    "TEMP",
    "PID",
    "TIME",
    "PROGRAM",
    "PROGRAM_BASE",
    "CACHE_DIR",
    "COMPANY",
    "PRODUCT",
    "VERSION",
    "HOME",
    "NONE",
    "NULL",
)


class _RetainingFormatter(Formatter):
    def get_value(self, key, args, kwargs):
        if isinstance(key, str):
            try:
                return kwargs[key]
            except KeyError:
                return "{%s}" % key
        else:
            return Formatter.get_value(self, key, args, kwargs)


def _expandProjectArg(arg, filename_arg, for_eval):
    def wrap(value):
        if for_eval:
            return repr(value)
        else:
            return value

    values = {
        "OS": wrap(getOS()),
        "Arch": wrap(getArchitecture()),
        "Flavor": wrap(getPythonFlavorName()),
        "Version": getNuitkaVersion(),
        "Commercial": wrap(getCommercialVersion()),
        "MAIN_DIRECTORY": wrap(os.path.dirname(filename_arg) or "."),
        "GIL": isPythonWithGil(),
    }

    if isLinux():
        dist_info = getLinuxDistribution()
    else:
        dist_info = "N/A", "N/A", "0"

    values["Linux_Distribution_Name"] = dist_info[0]
    values["Linux_Distribution_Base"] = dist_info[1] or dist_info[0]
    values["Linux_Distribution_Version"] = dist_info[2]

    if isWin32OrPosixWindows():
        values["WindowsRelease"] = getWindowsRelease()

    values.update(
        (
            (run_time_variable_name, "{%s}" % run_time_variable_name)
            for run_time_variable_name in run_time_variable_names
        )
    )

    arg = _RetainingFormatter().format(arg, **values)

    return arg


def getNuitkaProjectOptions(logger, filename_arg, module_mode):
    """Extract the Nuitka project options.

    Note: This is used by Nuitka project and test tools as well.
    """

    # Complex stuff, pylint: disable=too-many-branches,too-many-locals,too-many-statements

    if os.path.isdir(filename_arg):
        if module_mode:
            filename_arg = os.path.join(filename_arg, "__init__.py")
        else:
            filename_arg = os.path.join(filename_arg, "__main__.py")

    # The file specified may not exist, let the later parts of Nuitka handle this.
    try:
        contents_by_line = getFileContentByLine(filename_arg, "rb")
    except (OSError, IOError):
        return

    def sysexit(count, message):
        logger.sysexit("%s:%d %s" % (filename_arg, count + 1, message))

    execute_block = True
    expect_block = False

    cond_level = -1

    for line_number, line in enumerate(contents_by_line):
        match = re.match(b"^\\s*#(\\s*)nuitka-project(.*?):(.*)", line)

        if match:
            level, command, arg = match.groups()
            level = len(level)
            arg = arg.rstrip()

            # Check for empty conditional blocks.
            if expect_block and level <= cond_level:
                sysexit(
                    line_number,
                    "Error, 'nuitka-project-if|else' is expected to be followed by block start.",
                )

            expect_block = False

            if level == cond_level and command == b"-else":
                execute_block = not execute_block
            elif level <= cond_level:
                execute_block = True

            if level > cond_level and not execute_block:
                continue

            if str is not bytes:
                command = command.decode("utf8")
                arg = arg.decode("utf8")

            if command == "-if":
                if not arg.endswith(":"):
                    sysexit(
                        line_number,
                        "Error, 'nuitka-project-if' needs to start a block with a colon at line end.",
                    )

                arg = arg[:-1].strip()

                expanded = _expandProjectArg(arg, filename_arg, for_eval=True)

                with withNoSyntaxWarning():
                    r = eval(  # We allow the user to run any code, pylint: disable=eval-used
                        expanded
                    )

                # Likely mistakes, e.g. with "in" tests.
                if r is not True and r is not False:
                    sys.exit(
                        "Error, 'nuitka-project-if' condition %r (expanded to %r) does not yield boolean result %r"
                        % (arg, expanded, r)
                    )

                execute_block = r
                expect_block = True
                cond_level = level
            elif command == "-else":
                if arg:
                    sysexit(
                        line_number,
                        "Error, 'nuitka-project-else' cannot have argument.",
                    )

                if cond_level != level:
                    sysexit(
                        line_number,
                        "Error, 'nuitka-project-else' not currently allowed after nested nuitka-project-if.",
                    )

                expect_block = True
                cond_level = level
            elif command == "":
                arg = re.sub(r"""^([\w-]*=)(['"])(.*)\2$""", r"\1\3", arg.lstrip())

                if not arg:
                    continue

                yield _expandProjectArg(arg, filename_arg, for_eval=False)
            else:
                assert False, (command, line)


def _considerGithubWorkflowOptions(phase):
    try:
        github_option_index = sys.argv.index("--github-workflow-options")
    except ValueError:
        return

    import json

    early_names = (
        "main",
        "script-name",
        "enable-plugin",
        "enable-plugins",
        "disable-plugin",
        "disable-plugins",
        "user-plugin",
    )

    def filterByName(key):
        # Not for Nuitka at all.
        if key in (
            "nuitka-version",
            "working-directory",
            "access-token",
            "disable-cache",
        ):
            return False

        # Ignore platform specific options.
        if key.startswith("macos-") and not isMacOS():
            return False
        if (key.startswith("windows-") or key == "mingw64") and not isWin32Windows():
            return False
        if key.startswith("linux-") and not isLinux():
            return False

        if phase == "early":
            return key in early_names
        else:
            return key not in early_names

    options_added = []

    for key, value in json.loads(os.environ["NUITKA_WORKFLOW_INPUTS"]).items():
        if not value:
            continue

        if not filterByName(key):
            continue

        option_name = "--%s" % key

        if parser.isBooleanOption(option_name):
            if value == "false":
                continue

            options_added.append(option_name)
        elif parser.isListOption(option_name):
            for value in value.split("\n"):
                if not value.strip():
                    continue

                options_added.append("%s=%s" % (option_name, value))
        else:
            # Boolean disabled options from inactive plugins that default to off.
            if value == "false":
                continue

            options_added.append("%s=%s" % (option_name, value))

    sys.argv = (
        sys.argv[: github_option_index + (1 if phase == "early" else 0)]
        + options_added
        + sys.argv[github_option_index + 1 :]
    )


def parseOptions(logger):
    # Pretty complex code, having a small options parser and many details as
    # well as integrating with plugins and run modes. pylint: disable=too-many-branches

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

    filename_args = []
    module_mode = False

    # Options may be coming from GitHub workflow configuration as well.
    _considerGithubWorkflowOptions(phase="early")

    for count, arg in enumerate(sys.argv):
        if count == 0:
            continue

        if arg.startswith(("--main=", "--script-name=")):
            filename_args.append(arg.split("=", 1)[1])

        if arg == "--module":
            module_mode = True

        if arg[0] != "-":
            filename_args.append(arg)
            break

    for filename in filename_args:
        sys.argv = (
            [sys.argv[0]]
            + list(getNuitkaProjectOptions(logger, filename, module_mode))
            + sys.argv[1:]
        )

    # Next, lets activate plugins early, so they can inject more options to the parser.
    _considerPluginOptions(logger)

    # Options may be coming from GitHub workflow configuration as well.
    _considerGithubWorkflowOptions(phase="late")

    options, positional_args = parser.parse_args()

    if (
        not positional_args
        and not options.mains
        and not parser.hasNonCompilingAction(options)
    ):
        parser.print_help()

        logger.sysexit(
            """
Error, need filename argument with python module or main program."""
        )

    if not options.immediate_execution and len(positional_args) > 1:
        parser.print_help()

        logger.sysexit(
            """
Error, specify only one positional argument unless "--run" is specified to
pass them to the compiled program execution."""
        )

    return is_nuitka_run, options, positional_args, extra_args


def runSpecialCommandsFromOptions(options):
    if options.plugin_list:
        from nuitka.plugins.Plugins import listPlugins

        listPlugins()
        sys.exit(0)

    if options.list_package_dlls:
        from nuitka.tools.scanning.DisplayPackageDLLs import displayDLLs

        displayDLLs(options.list_package_dlls)
        sys.exit(0)

    if options.list_package_data:
        from nuitka.tools.scanning.DisplayPackageData import displayPackageData

        displayPackageData(options.list_package_data)
        sys.exit(0)

    if options.edit_module_code:
        from nuitka.tools.general.find_module.FindModuleCode import (
            editModuleCode,
        )

        editModuleCode(options.edit_module_code)
        sys.exit(0)

    if options.create_environment_from_report:
        from nuitka.tools.environments.CreateEnvironment import (
            createEnvironmentFromReport,
        )

        createEnvironmentFromReport(
            environment_folder=os.path.expanduser(
                options.create_environment_from_report
            ),
            report_filename=os.path.expanduser(options.compilation_report_filename),
        )
        sys.exit(0)


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
