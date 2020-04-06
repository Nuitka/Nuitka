#!/usr/bin/env python
#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#

""" Runner for program tests of Nuitka.

Program tests are typically aiming at checking specific module constellations
and making sure the details are being right there. These are synthetic small
programs, each of which try to demonstrate one or more points or special
behaviour.

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

from nuitka.tools.testing.Common import (
    compareWithCPython,
    createSearchMode,
    my_print,
    reportSkip,
    setup,
    withPythonPathChange,
)


def getMainProgramFilename(filename):
    for filename_main in os.listdir(filename):
        if filename_main.endswith(("Main.py", "Main")):
            return filename_main

    sys.exit(
        """\
Error, no file ends with 'Main.py' or 'Main' in %s, incomplete test case."""
        % (filename)
    )


def main():
    # Complex stuff, even more should become common code though.
    # pylint: disable=too-many-branches,too-many-statements

    python_version = setup(needs_io_encoding=True)

    search_mode = createSearchMode()

    extra_options = os.environ.get("NUITKA_EXTRA_OPTIONS", "")

    for filename in sorted(os.listdir(".")):
        if (
            not os.path.isdir(filename)
            or filename.endswith(".build")
            or filename.endswith(".dist")
        ):
            continue

        filename = os.path.relpath(filename)

        # For these, we expect that they will fail.
        expected_errors = [
            "module_exits",
            "main_raises",
            "main_raises2",
            "package_contains_main",
        ]

        # After Python3 those have been made to work.
        if python_version < "3.5":
            expected_errors.append("cyclic_imports")

        # Allowed with Python3, packages need no more "__init__.py"
        if python_version < "3":
            expected_errors.append("package_missing_init")

        # Allowed with Python3.5 only:
        if python_version < "3.5":
            expected_errors.append("package_init_issue")

        # Allowed with Python3, name imports can be module imports
        if python_version < "3":
            expected_errors.append("named_imports")

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
            "pkgutil_itermodules",
        ):
            extra_flags.append("ignore_warnings")

        extra_flags.append("remove_output")

        extra_flags.append("recurse_all")

        # Use the original __file__ value, at least one case warns about things
        # with filename included, but for pkgutil iteration, make sure we do not
        # see original Python dirs.
        if filename != "pkgutil_itermodules":
            extra_flags.append("original_file")
        else:
            extra_flags.append("runtime_file")

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
            if python_version < "3":
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
            if os.name == "nt":
                extra_flags += ("plugin_enable:multiprocessing", "ignore_infos")

            elif sys.platform == "darwin" and python_version >= "3.8":
                reportSkip("Hangs for unknown reasons", ".", filename)
                continue
        else:
            os.environ["NUITKA_EXTRA_OPTIONS"] = extra_options

        active = search_mode.consider(dirname=None, filename=filename)

        if active:
            my_print("Consider output of recursively compiled program:", filename)

            filename_main = getMainProgramFilename(filename)

            extra_python_path = [
                os.path.abspath(os.path.join(filename, entry))
                for entry in os.listdir(filename)
                if entry.startswith("path")
            ]

            with withPythonPathChange(extra_python_path):
                compareWithCPython(
                    dirname=filename,
                    filename=filename_main,
                    extra_flags=extra_flags,
                    search_mode=search_mode,
                    needs_2to3=False,
                )

            if search_mode.abortIfExecuted():
                break

    search_mode.finish()


if __name__ == "__main__":
    main()
