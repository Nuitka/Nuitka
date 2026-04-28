#!/usr/bin/env python
#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Test Nuitka compiling itself and compiling itself in compiled form again.

This should not only give no errors, but the same source for modules being
compiled when Nuitka is running compiled and uncompiled, so we can discover
changes in order of execution in this test.
"""

import os
import sys

# Find nuitka package relative to us.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    ),
)

# isort:start

import shutil
import subprocess

from nuitka.build.SconsInterface import getInlineSconsLibPath
from nuitka.options.CommandLineOptionsTools import makeOptionsParser
from nuitka.reports.CompilationReportReader import (
    getCompilationOutputBinary,
    parseCompilationReport,
)
from nuitka.tools.Basics import addPYTHONPATH
from nuitka.tools.testing.Common import (
    getPythonSysPath,
    getTempDir,
    my_print,
    setup,
    test_logger,
    withPythonPathChange,
)
from nuitka.utils.Diffs import compareDirectories
from nuitka.utils.Execution import wrapCommandForDebuggerForSubprocess
from nuitka.utils.FileOperations import (
    copyTree,
    deleteFile,
    getFileList,
    getSubDirectories,
    listDir,
    removeDirectory,
)
from nuitka.utils.Importing import getExtensionModuleSuffix
from nuitka.Version import getCommercialVersion

nuitka_main_path = os.path.join("..", "..", "bin", "nuitka")

tmp_dir = getTempDir()

# Cannot detect this more automatic, so we need to list them, avoiding
# the ones not needed.
PACKAGE_LIST = [
    "nuitka",
    "nuitka/build",
    "nuitka/code_generation",
    "nuitka/code_generation/c_types",
    "nuitka/code_generation/templates",
    "nuitka/containers",
    "nuitka/finalizations",
    "nuitka/freezer",
    "nuitka/importing",
    "nuitka/nodes",
    "nuitka/nodes/shapes",
    "nuitka/optimizations",
    "nuitka/options",
    "nuitka/pgo",
    "nuitka/plugins",
    "nuitka/plugins/commercial",
    "nuitka/plugins/standard",
    "nuitka/reports",
    "nuitka/specs",
    "nuitka/tree",
    "nuitka/format",
    "nuitka/package_config",
    "nuitka/utils",
]

if not getCommercialVersion():
    PACKAGE_LIST.remove("nuitka/plugins/commercial")

exe_suffix = ".exe" if os.name == "nt" else ".bin"
nuitka_runner_binary = "nuitka-runner" + exe_suffix
data_composer_main = "DataComposer.py"
scons_main = "scons.py"
pass_numbers = (1, 2, 3, 4, 5)


def _traceCompilation(path, pass_number):
    test_logger.info("Compiling '%s' (PASS %d)." % (path, pass_number))


def _updateDataComposerMain(filename, use_checkout_path):
    with open(filename, "w") as output_file:
        if use_checkout_path:
            output_file.write("""\
#!/usr/bin/env python

import os
import sys

sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    ),
)

from nuitka.tools.data_composer.DataComposer import main

del sys.path[0]

sys.path = [
    path_element
    for path_element in sys.path
    if os.path.dirname(os.path.abspath(__file__)) != path_element
]

main()
""")
        else:
            output_file.write("""\
#!/usr/bin/env python

from nuitka.tools.data_composer.DataComposer import main

main()
""")


def _updateNuitkaRunnerMain():
    with open("nuitka-runner.py", "w") as output_file:
        output_file.write("""\
#!/usr/bin/env python

\"\"\"Launcher for reflected Nuitka compiler runs.\"\"\"

import os
import sys

sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    ),
)

import nuitka.__main__  # false alarm, pylint: disable=I0021,no-name-in-module

del sys.path[0]

sys.path = [
    path_element
    for path_element in sys.path
    if os.path.dirname(os.path.abspath(__file__)) != path_element
]

nuitka.__main__.main()
""")


def _updateSconsMain(filename):
    with open(filename, "w") as output_file:
        output_file.write("""\
#!/usr/bin/env python

import os

import SCons
import SCons.Script

os.environ["SCONS_LIB_DIR"] = os.path.dirname(SCons.__file__)

SCons.Script.main()
""")


def _createMultidistBinaryAlias(binary_path, alias_name):
    alias_path = os.path.join(os.path.dirname(binary_path), alias_name + exe_suffix)

    deleteFile(alias_path, must_exist=False)

    try:
        os.link(binary_path, alias_path)
    except OSError:
        shutil.copy2(binary_path, alias_path)

    return alias_path


def _parsePassNumber(pass_number, option_name):
    try:
        pass_number = int(pass_number)
    except ValueError:
        return test_logger.sysexit(
            "The '%s' option got invalid pass number '%s'." % (option_name, pass_number)
        )

    if pass_number not in pass_numbers:
        return test_logger.sysexit(
            "The '%s' option got pass number '%s' outside supported range %d-%d."
            % (option_name, pass_number, pass_numbers[0], pass_numbers[-1])
        )

    return pass_number


def _parsePassSpec(pass_spec, option_name):
    result = set()

    for pass_item in pass_spec.split(","):
        pass_item = pass_item.strip()

        if not pass_item:
            continue

        if "-" in pass_item:
            start_pass, stop_pass = pass_item.split("-", 1)

            start_pass = _parsePassNumber(start_pass, option_name)
            stop_pass = _parsePassNumber(stop_pass, option_name)

            if start_pass > stop_pass:
                return test_logger.sysexit(
                    "The '%s' option got descending pass range '%s'."
                    % (option_name, pass_item)
                )

            for pass_number in range(start_pass, stop_pass + 1):
                result.add(pass_number)
        else:
            result.add(_parsePassNumber(pass_item, option_name))

    if not result:
        return test_logger.sysexit(
            "The '%s' option needs at least one pass number." % option_name
        )

    return result


def _recordPassSelection(option, opt_str, value, parser, operation):
    pass_selection_operations = parser.values.pass_selection_operations

    if pass_selection_operations is None:
        pass_selection_operations = []
        parser.values.pass_selection_operations = pass_selection_operations

    pass_selection_operations.append((operation, _parsePassSpec(value, opt_str)))


def _parseArgs():
    parser = makeOptionsParser(usage=None, epilog=None)
    parser.error = test_logger.sysexit

    parser.set_defaults(pass_selection_operations=None)

    parser.add_option(
        "--run-passes",
        action="callback",
        type="string",
        callback=_recordPassSelection,
        callback_args=("run",),
        help="""\
Run only the selected passes, e.g. '1,3-5'. Can be given multiple times.""",
    )

    parser.add_option(
        "--skip-passes",
        action="callback",
        type="string",
        callback=_recordPassSelection,
        callback_args=("skip",),
        help="""\
Skip selected passes from the current pass set, e.g. '2,4'. Can be given multiple times.""",
    )

    options, positional_args = parser.parse_args()

    enabled_passes = set(pass_numbers)

    if options.pass_selection_operations:
        for operation, selected_passes in options.pass_selection_operations:
            if operation == "run":
                enabled_passes = selected_passes
            else:
                enabled_passes.difference_update(selected_passes)

    return enabled_passes, positional_args


def executePASS1():
    test_logger.info(
        "PASS 1: Compiling to many compiled modules from compiler running from .py files."
    )

    base_dir = os.path.join("..", "..")

    for package in PACKAGE_LIST:
        package = package.replace("/", os.path.sep)

        source_dir = os.path.join(base_dir, package)
        target_dir = package

        removeDirectory(
            path=target_dir,
            logger=test_logger,
            ignore_errors=False,
            extra_recommendation=None,
        )

        os.mkdir(target_dir)

        for path, filename in listDir(target_dir):
            if filename.endswith((".so", ".dylib")):
                os.unlink(path)

        for path, filename in listDir(source_dir):
            if not filename.endswith(".py"):
                continue

            if filename.startswith(".#"):
                continue

            if filename != "__init__.py":
                _traceCompilation(path=path, pass_number=1)

                command = [
                    os.environ["PYTHON"],
                    nuitka_main_path,
                    "--mode=module",
                    "--nofollow-imports",
                    "--output-dir=%s" % target_dir,
                    "--no-pyi-file",
                    path,
                ]
                command += os.getenv("NUITKA_EXTRA_OPTIONS", "").split()

                my_print("Command: ", " ".join(command))

                result = subprocess.call(command)

                if result != 0:
                    sys.exit(result)
            else:
                shutil.copyfile(path, os.path.join(target_dir, filename))

    _traceCompilation(path=nuitka_main_path, pass_number=1)

    _updateNuitkaRunnerMain()
    _updateDataComposerMain(data_composer_main, use_checkout_path=True)

    command = [
        os.environ["PYTHON"],
        nuitka_main_path,
        "--nofollow-imports",
        "--output-dir=.",
        "--python-flag=no_site",
        "--main=nuitka-runner.py",
        "--main=%s" % data_composer_main,
    ]
    command += os.getenv("NUITKA_EXTRA_OPTIONS", "").split()

    my_print("Command: ", " ".join(command))

    try:
        result = subprocess.call(command)
    finally:
        deleteFile(path=data_composer_main, must_exist=False)

    if result != 0:
        sys.exit(result)

    # Keep the binary name aligned with the multidist entry point name.
    deleteFile(path="nuitka" + exe_suffix, must_exist=False)

    scons_inline_copy_path = os.path.join(base_dir, "nuitka", "build", "inline_copy")

    if os.path.exists(scons_inline_copy_path):
        copyTree(scons_inline_copy_path, os.path.join("nuitka", "build", "inline_copy"))

    # Copy required data files.
    for filename in (
        "nuitka/build/Backend.scons",
        "nuitka/build/CCompilerVersion.scons",
        "nuitka/build/Offsets.scons",
        "nuitka/build/Onefile.scons",
        "nuitka/plugins/standard/standard.nuitka-package.config.yml",
        "nuitka/plugins/standard/stdlib3.nuitka-package.config.yml",
        "nuitka/plugins/standard/stdlib2.nuitka-package.config.yml",
    ):
        shutil.copyfile(
            os.path.join(base_dir, filename),
            filename,
        )

    copyTree(
        os.path.join(base_dir, "nuitka", "code_generation", "templates_c"),
        os.path.join("nuitka", "code_generation", "templates_c"),
    )

    copyTree(
        os.path.join(base_dir, "nuitka", "build", "static_src"),
        os.path.join("nuitka", "build", "static_src"),
    )
    copyTree(
        os.path.join(base_dir, "nuitka", "build", "include"),
        os.path.join("nuitka", "build", "include"),
    )

    # The data composer tool, use it by source.
    copyTree(
        os.path.join(base_dir, "nuitka", "tools"),
        os.path.join("nuitka", "tools"),
    )

    test_logger.info("OK.")


def compileAndCompareWith(nuitka, pass_number):
    if "PYTHONHASHSEED" not in os.environ:
        os.environ["PYTHONHASHSEED"] = "0"
    if "PYTHON_FROZEN_MODULES" not in os.environ:
        os.environ["PYTHON_FROZEN_MODULES"] = "off"

    base_dir = os.path.join("..", "..")

    for package in PACKAGE_LIST:
        package = package.replace("/", os.path.sep)

        source_dir = os.path.join(base_dir, package)

        for path, filename in listDir(source_dir):
            if not filename.endswith(".py"):
                continue

            if filename.startswith(".#"):
                continue

            path = os.path.join(source_dir, filename)

            if filename != "__init__.py":
                _traceCompilation(path=path, pass_number=pass_number)

                target = filename.replace(".py", ".build")

                target_dir = os.path.join(tmp_dir, target)

                removeDirectory(
                    logger=test_logger,
                    path=target_dir,
                    ignore_errors=False,
                    extra_recommendation=None,
                )

                command = [
                    nuitka,
                    "--mode=module",
                    "--output-dir=%s" % tmp_dir,
                    "--no-pyi-file",
                    "--nofollow-imports",
                    path,
                ]
                command += os.getenv("NUITKA_EXTRA_OPTIONS", "").split()

                my_print("Command: ", " ".join(command))
                exit_nuitka = subprocess.call(command)

                # In case of segfault or assertion triggered, run in debugger.
                if exit_nuitka in (-11, -6) and sys.platform != "nt":
                    command2 = wrapCommandForDebuggerForSubprocess(
                        command=command, debugger=os.getenv("NUITKA_DEBUGGER_CHOICE")
                    )
                    subprocess.call(command2)

                if exit_nuitka != 0:
                    my_print("An error exit %s occurred, aborting." % exit_nuitka)
                    sys.exit(exit_nuitka)

                has_diff = compareDirectories(
                    logger=test_logger,
                    my_print=my_print,
                    dir1=os.path.join(package, target),
                    dir2=target_dir,
                    ignore_suffixes=(
                        ".o",
                        ".os",
                        ".obj",
                        ".dblite",  # spell-checker: ignore dblite
                        ".tmp",
                        ".sconsign",  # spell-checker: ignore sconsign
                        ".txt",
                        ".bin",
                        ".const",
                        ".exp",
                        ".scons",
                    ),
                    ignore_substrings=(
                        "cache-",
                        "scons-debug",
                    ),
                )

                if has_diff:
                    sys.exit("There were differences!")

                shutil.rmtree(target_dir)

                for preferred in (True, False):
                    target_filename = filename.replace(
                        ".py", getExtensionModuleSuffix(preferred=preferred)
                    )

                    deleteFile(
                        path=os.path.join(tmp_dir, target_filename), must_exist=False
                    )


def executePASS2():
    test_logger.info(
        "PASS 2: Compiling from compiler running from entry '.exe' and many extension files."
    )

    with withPythonPathChange(getPythonSysPath()):
        # Windows will load the compiled modules (pyd) only from PYTHONPATH, so we
        # have to add it.
        if os.name == "nt":
            addPYTHONPATH(PACKAGE_LIST)

        compileAndCompareWith(
            nuitka=os.path.join(".", nuitka_runner_binary), pass_number=2
        )

    # Cleanup compiled modules that would otherwise confuse PASS3, but keep the
    # PASS1 ".build" directories as comparison baseline for PASS4 and repeated
    # late-pass reruns.
    for filename in getFileList("nuitka", only_suffixes=(".so", ".pyd")):
        deleteFile(filename, must_exist=True)

    test_logger.info("OK.")


def executePASS3():
    test_logger.info(
        "PASS 3: Compiling from compiler running from .py files to single .exe."
    )

    exe_path = os.path.join(tmp_dir, "nuitka-runner" + exe_suffix)

    if os.path.exists(exe_path):
        os.unlink(exe_path)

    build_path = os.path.join(tmp_dir, "nuitka-runner.build")

    if os.path.exists(build_path):
        shutil.rmtree(build_path)

    base_dir = os.path.abspath(os.path.join("..", ".."))
    helper_dir = os.path.join(tmp_dir, "pass3-main")

    if not os.path.exists(helper_dir):
        os.makedirs(helper_dir)

    runner_main_path = os.path.join(helper_dir, "nuitka-runner.py")
    data_composer_main_path = os.path.join(helper_dir, data_composer_main)
    scons_main_path = os.path.join(helper_dir, scons_main)

    path = os.path.join("..", "..", "bin", "nuitka")

    _traceCompilation(path=path, pass_number=3)

    with withPythonPathChange((base_dir, getInlineSconsLibPath())):
        with open(runner_main_path, "w") as output_file:
            output_file.write("""\
#!/usr/bin/env python

\"\"\"Launcher for source-based Nuitka compiler runs.\"\"\"

import nuitka.__main__  # false alarm, pylint: disable=I0021,no-name-in-module

nuitka.__main__.main()
""")

        _updateDataComposerMain(data_composer_main_path, use_checkout_path=False)
        _updateSconsMain(scons_main_path)

        command = [
            os.environ["PYTHON"],
            os.path.join(base_dir, "bin", "nuitka"),
            "--output-dir=%s" % tmp_dir,
            "--python-flag=-S",
            "--follow-imports",
            "--include-package=nuitka.plugins.standard",
            "--nofollow-import-to=*-postLoad",
            "--nofollow-import-to=pip",
            "--report=%s" % os.path.abspath("compilation-report-pass3.xml"),
            "--main=%s" % runner_main_path,
            "--main=%s" % data_composer_main_path,
            "--main=%s" % scons_main_path,
        ]

        my_print("Command: ", " ".join(command))
        result = subprocess.call(command, cwd=base_dir)

    if result != 0:
        sys.exit(result)

    _createMultidistBinaryAlias(exe_path, "scons")

    shutil.rmtree(build_path)

    test_logger.info("OK.")


def executePASS4():
    test_logger.info("PASS 4: Compiling the compiler running from single exe.")

    compilation_report = parseCompilationReport("compilation-report-pass3.xml")

    exe_path = getCompilationOutputBinary(
        compilation_report=compilation_report,
        prefixes=(("${cwd}", os.getcwd()),),
    )

    # The source compiler uses the host Python import path for optional
    # non-stdlib modules like "pkg_resources", so mirror that here to keep
    # import lowering decisions stable for comparisons.
    with withPythonPathChange(
        getPythonSysPath().split(os.pathsep) + [os.path.join("..", "..")]
    ):
        compileAndCompareWith(exe_path, pass_number=4)

    test_logger.info("OK.")


def executePASS5():
    my_print(
        "PASS 5: Compiling the compiler 'nuitka' package to single extension module."
    )

    path = os.path.join("..", "..", "nuitka")

    command = [
        os.environ["PYTHON"],
        nuitka_main_path,
        "--output-dir=%s" % tmp_dir,
        "--include-plugin-dir=%s" % path,
        "--nofollow-import-to=nuitka.build.inline_copy",
        "--nofollow-import-to=nuitka.build.include",
        "--nofollow-import-to=nuitka.build.static_src",
        "--nofollow-import-to=nuitka.tools",
        "--mode=module",
        path,
    ]

    result = subprocess.call(command)

    if result != 0:
        sys.exit(result)

    for preferred in (True, False):
        candidate = "nuitka" + getExtensionModuleSuffix(preferred=preferred)

        deleteFile(candidate, must_exist=False)

    os.unlink(os.path.join(tmp_dir, "nuitka.pyi"))
    shutil.rmtree(os.path.join(tmp_dir, "nuitka.build"))


def main():
    enabled_passes, _unused_positional_args = _parseArgs()

    setup(needs_io_encoding=True)

    if enabled_passes != set(pass_numbers):
        selected_passes = (
            ",".join(str(pass_number) for pass_number in sorted(enabled_passes))
            or "none"
        )
        test_logger.info("Selected passes: %s." % selected_passes)

    for pass_number, pass_function in (
        (1, executePASS1),
        (2, executePASS2),
        (3, executePASS3),
        (4, executePASS4),
        (5, executePASS5),
    ):
        if pass_number not in enabled_passes:
            test_logger.info("PASS %d: Skipped by option." % pass_number)
            continue

        pass_function()


if __name__ == "__main__":
    main()

#     Python tests originally created or extracted from other peoples work. The
#     parts were too small to be protected.
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
