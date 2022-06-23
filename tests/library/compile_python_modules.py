#!/usr/bin/env python
#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

""" This test runner compiles all Python files as a module.

This is a test to achieve some coverage, it will only find assertions of
within Nuitka or warnings from the C compiler. Code will not be run
normally.

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

import subprocess

from nuitka.tools.testing.Common import (
    checkCompilesNotWithCPython,
    compileLibraryTest,
    createSearchMode,
    getPythonArch,
    getPythonVendor,
    getTempDir,
    my_print,
    setup,
)
from nuitka.utils.Importing import getSharedLibrarySuffix

python_version = setup(suite="python_modules", needs_io_encoding=True)
python_vendor = getPythonVendor()
python_arch = getPythonArch()

search_mode = createSearchMode()

tmp_dir = getTempDir()

ignore_list = (
    "__phello__.foo.py",  # Triggers error for "." in module name
    "idnadata",  # Avoid too complex code for main program.
    "joined_strings.py",
    # Incredible amount of memory in C compiler for test code
    "test_spin.py",
    # Uses outside modules up the chain
    "cheshire_tomography.py",
)

nosyntax_errors = (
    # No syntax error with Python2 compileall, but run time only:
    "_identifier.py",
    "bench.py",
    "_tweedie_compound_poisson.py",
    "session.py",
)


def decide(_root, filename):
    return (
        filename.endswith(".py")
        and filename not in ignore_list
        and "(" not in filename
        and filename.count(".") == 1
    )


def action(stage_dir, _root, path):
    command = [
        sys.executable,
        os.path.join("..", "..", "bin", "nuitka"),
        "--module",
        "--output-dir=%s" % stage_dir,
        "--remove-output",
        "--quiet",
        "--nofollow-imports",
        "--enable-plugin=pylint-warnings",
    ]

    command += os.environ.get("NUITKA_EXTRA_OPTIONS", "").split()

    command.append(path)

    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError:
        if os.path.basename(path) in nosyntax_errors:
            my_print("Syntax error is known unreliable with file file.")
        else:
            my_print("Falling back to full comparison due to error exit.")

            checkCompilesNotWithCPython(
                dirname=None, filename=path, search_mode=search_mode
            )
    else:
        my_print("OK")

        suffix = getSharedLibrarySuffix(preferred=True)

        target_filename = os.path.basename(path)[:-3] + suffix
        target_filename = target_filename.replace("(", "").replace(")", "")

        os.unlink(os.path.join(stage_dir, target_filename))


compileLibraryTest(
    search_mode=search_mode,
    stage_dir=os.path.join(
        tmp_dir,
        "compile_library_%s-%s-%s"
        % (".".join(str(d) for d in python_version), python_arch, python_vendor),
    ),
    decide=decide,
    action=action,
)

search_mode.finish()
