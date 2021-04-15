#!/usr/bin/env python
#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#

""" Runner for plugins tests of Nuitka.

Plugin tests are typically aiming at covering plugin interfaces and their
correctness, not concrete standard plugins.
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
    setup(needs_io_encoding=True)

    search_mode = createSearchMode()

    extra_options = os.environ.get("NUITKA_EXTRA_OPTIONS", "")

    # TODO: Add a directory test case scanner instead of duplicating this kind of code.
    for filename in sorted(os.listdir(".")):
        if (
            not os.path.isdir(filename)
            or filename.endswith(".build")
            or filename.endswith(".dist")
        ):
            continue

        filename = os.path.relpath(filename)

        extra_flags = ["expect_success"]

        # We annotate some tests, use that to lower warnings.
        extra_flags.append("plugin_enable:pylint-warnings")
        extra_flags.append("remove_output")
        extra_flags.append("recurse_all")

        plugin_files = [p for p in os.listdir(filename) if p.endswith("-plugin.py")]

        assert plugin_files
        extra_flags.extend(
            "user_plugin:" + os.path.abspath(os.path.join(filename, p))
            for p in plugin_files
        )

        if filename == "parameters":
            os.environ["NUITKA_EXTRA_OPTIONS"] = extra_options + " --trace-my-plugin"
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

    search_mode.finish()


if __name__ == "__main__":
    main()
