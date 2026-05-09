#!/usr/bin/env python
#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Runner for program tests of Nuitka.

Program tests are typically aiming at checking specific module constellations
and making sure the details are being right there. These are synthetic small
programs, each of which try to demonstrate one or more points or special
behavior.

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

from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.reports.CompilationReportReader import (
    extractModulesUsedByModule,
    parseCompilationReport,
)
from nuitka.tools.testing.Common import (
    checkTestRequirements,
    compareWithCPython,
    createSearchMode,
    my_print,
    reportSkip,
    scanDirectoryForTestCaseFolders,
    setup,
    test_logger,
    withPythonPathChange,
)
from nuitka.utils.Execution import check_call
from nuitka.utils.FileOperations import (
    makePath,
    putTextFileContents,
    resetDirectory,
)


def checkMultiprocessingUsingReport(filename, python_version):
    compilation_report = parseCompilationReport("compilation-report-%s.xml" % filename)

    parent_main_module = None

    for module_node in compilation_report.findall("module"):
        if module_node.attrib["name"] == "__parents_main__":
            parent_main_module = module_node
            break

    assert parent_main_module is not None, [
        module_node.attrib["name"]
        for module_node in compilation_report.findall("module")
    ]
    assert (
        parent_main_module.attrib["reason"]
        == "Auto enable multiprocessing/anyio freeze support"
    ), parent_main_module.attrib

    # On Python 2, the fake module is executed directly for freeze support.
    # On Python 3, the multiprocessing post-load helper imports it.
    if python_version < (3,):
        return

    modules_used = extractModulesUsedByModule(
        compilation_report=compilation_report,
        module_name="multiprocessing-postLoad",
    )

    assert modules_used["__parents_main__"]["finding"] == "fake", modules_used


def _makeBytecodeOnlyModule(filename, source_code):
    putTextFileContents(filename=filename, contents=source_code, encoding="utf8")

    try:
        check_call(
            (
                os.environ["PYTHON"],
                "-c",
                # spell-checker: ignore cfile,doraise
                "import py_compile,sys; py_compile.compile(sys.argv[1], cfile=sys.argv[1] + 'c', doraise=True)",
                filename,
            )
        )
    finally:
        if os.path.exists(filename):
            os.unlink(filename)


def updateBytecodeOnlyImportPath(test_directory):
    bytecode_only_path = os.path.join(test_directory, "path1")

    resetDirectory(
        path=bytecode_only_path,
        logger=test_logger,
        ignore_errors=True,
        extra_recommendation=None,
    )

    _makeBytecodeOnlyModule(
        filename=os.path.join(bytecode_only_path, "bytecode_only_module.py"),
        source_code='module_value = "module-bytecode-only"\n',
    )

    package_dir = os.path.join(bytecode_only_path, "bytecode_only_package")
    makePath(package_dir)

    _makeBytecodeOnlyModule(
        filename=os.path.join(package_dir, "__init__.py"),
        source_code='package_value = "package-bytecode-only"\n',
    )

    _makeBytecodeOnlyModule(
        filename=os.path.join(package_dir, "submodule.py"),
        source_code='submodule_value = "submodule-bytecode-only"\n',
    )


def main():
    # Complex stuff, even more should become common code though.
    # pylint: disable=too-many-branches,too-many-statements

    python_version = setup(suite="programs", needs_io_encoding=True)

    search_mode = createSearchMode()

    extra_options = os.getenv("NUITKA_EXTRA_OPTIONS", "")

    for filename, filename_main in scanDirectoryForTestCaseFolders("."):
        active = search_mode.consider(dirname=None, filename=filename)

        if not active:
            continue

        # For these, we expect that they will fail.
        expected_errors = [
            "module_exits",
            "main_raises",
            "main_raises2",
            "package_contains_main",
        ]

        # After Python3 those have been made to work.
        if python_version < (3, 5):
            expected_errors.append("cyclic_imports")

        # Allowed with Python3, packages need no more "__init__.py"
        if python_version < (3,):
            expected_errors.append("package_missing_init")

        # Allowed with Python3.5 only:
        if python_version < (3, 5):
            expected_errors.append("package_init_issue")

        # Allowed with Python3, name imports can be module imports
        if python_version < (3,):
            expected_errors.append("named_imports")

        extra_variant = []

        if filename not in expected_errors:
            extra_flags = ["expect_success"]
        else:
            extra_flags = ["expect_failure"]

        # We annotate some tests, use that to lower warnings.
        extra_flags.append("plugin_enable:pylint-warnings")

        if filename in (
            "reimport_main_static",
            "package_missing_init",
            "dash_import",
            "package_contains_main",
            "case_imports3",
            "import_variants",
            "package_init_import",
            "pkgutil_iter_modules",
        ):
            extra_flags.append("ignore_warnings")

        extra_flags.append("remove_output")

        extra_flags.append("--follow-imports")

        # Run it as a package and also as directory.
        if filename == "package_program":
            # Not really supported for 2.6
            if python_version >= (2, 7):
                extra_variant.append("--python-flag=-m")

        # Cannot include the files with syntax errors, these would then become
        # ImportError, but that's not the test. In all other cases, use two
        # step execution, which will not add the program original source to
        # PYTHONPATH.
        if filename != "syntax_errors":
            extra_flags.append("two_step_execution")
        else:
            extra_flags.append("binary_python_path")

        if filename == "plugin_import":
            os.environ["NUITKA_EXTRA_OPTIONS"] = (
                extra_options + " --include-package=some_package"
            )
        elif filename == "reimport_main_dynamic":
            if python_version < (3,):
                os.environ["NUITKA_EXTRA_OPTIONS"] = (
                    extra_options
                    + " --include-plugin-directory=%s" % (os.path.abspath(filename))
                )
            else:
                os.environ["NUITKA_EXTRA_OPTIONS"] = (
                    extra_options
                    + " --include-plugin-files=%s/*.py" % (os.path.abspath(filename))
                )

            extra_flags.append("ignore_warnings")
        elif filename == "multiprocessing_using":
            extra_flags.append("--report=compilation-report-%s.xml" % filename)
        else:
            os.environ["NUITKA_EXTRA_OPTIONS"] = extra_options

        requirements_met, error_message = checkTestRequirements(
            os.path.join(filename, filename_main)
        )
        if not requirements_met:
            reportSkip(error_message, ".", filename)
            continue

        my_print("Consider output of recursively compiled program:", filename)

        if filename == "bytecode_only_import":
            updateBytecodeOnlyImportPath(filename)

        extra_python_path = [
            os.path.abspath(os.path.join(filename, entry))
            for entry in os.listdir(filename)
            if entry.startswith("path")
        ]

        if extra_python_path:
            my_print("Applying extra PYTHONPATH %r." % extra_python_path)

        with withPythonPathChange(extra_python_path):
            test_variants = OrderedDict((("", extra_flags),))

            if extra_variant:
                test_variants["variant"] = extra_flags + extra_variant

            compareWithCPython(
                dirname=filename,
                filename=filename_main,
                extra_flags=test_variants,
                search_mode=search_mode,
            )

            if filename == "multiprocessing_using":
                checkMultiprocessingUsingReport(filename, python_version)

    search_mode.finish()


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
