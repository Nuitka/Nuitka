#     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" PyLint handling for Nuitka.

Our usage of PyLint also works around a few issues that PyLint
has.

"""

from __future__ import print_function

import os
import subprocess
import sys

pylint_version = None

def checkVersion():
    # pylint: disable=global-statement
    global pylint_version

    if pylint_version is None:
        pylint_version = subprocess.check_output(
            ["pylint", "--version"],
            stderr = open(os.devnull, 'w')
        )

        pylint_version = pylint_version.split(b"\n")[0].split()[-1]

    if pylint_version < b"1.6.5":
        sys.exit("Error, needs PyLint 1.6.5 or higher not %r." % pylint_version)


# Disabled globally:
#
# no-init: Class has no __init__ method
# Who cares, we are using overrides that don't need to change object init a lot
# and rarely ever made a mistake with forgetting to call used __init__ of the
# parent.
#
# I0011: Locally disabling W....
# Strange one anyway, we want to locally disable stuff. And that just makes it
# a different warning. Amazing. Luckily we can decide to ignore that globally
# then.
#
# I0012: Locally enabling W....
# Sure, we disabled it for a block, and re-enabled it then.
#
# C0326: No space allowed...
# Our spaces before keyword argument calls are not allowed, and this is
# not possible to distinguish.
#
# C0330: Wrong hanging line indentation
# No it's not wrong.
#
# E1120 / E1123: ....
# Constructor call checks frequently fail miserably, so this is full of
# mysterious false alarms, while it's unlikely to help much.
#
# E1103: Instance of 'x' has no 'y' member but some types could not be inferred
# Rarely is this any help, but it's full of false alarms.
#
# W0632: Possible unbalanced tuple unpacking with sequence defined at ...
# It's not really good at guessing these things.
#
# W1504: Using type() instead of isinstance() for a typecheck.
# Nuitka is all about exact type checks, so this doesn't apply
#
# C0123: Using type() instead of isinstance() for a typecheck.
# Nuitka is all about exact type checks, so this doesn't apply
#
# C0413: Import "..." should be placed at the top of the module
# There is no harm to this and imports are deal with by isort binary.
#
# C0411: external import "external" comes before "local"
# There is no harm to this and imports are deal with by "isort" binary.
#
# R0204: Redefinition of var type from x to y
# I do this all the time, e.g. to convert "str" to "unicode", or "list" to "str".
#
# R1705: Unnecessary "else" after "return"
# Frequently we use multiple branches where each returns.

def getOptions():
    checkVersion()

    default_pylint_options = """\
--rcfile=/dev/null
--disable=I0011,I0012,no-init,C0326,C0330,E1103,W0632,W1504,C0123,C0411,C0413,R0204,similar-code,cyclic-import,duplicate-code
--enable=useless-suppression
--msg-template="{path}:{line} {msg_id} {symbol} {obj} {msg}"
--reports=no
--persistent=no
--method-rgx=[a-z_][a-zA-Z0-9_]{2,40}$
--module-rgx=.*
--function-rgx=.*
--variable-rgx=.*
--argument-rgx=.*
--dummy-variables-rgx=_.*|trace_collection
--const-rgx=.*
--max-line-length=120
--no-docstring-rgx=.*
--max-module-lines=5000
--min-public-methods=0
--max-public-methods=100
--max-args=11
--max-parents=10
--max-nested-blocks=10
--max-bool-expr=10\
""".split('\n')



    if pylint_version >= b"1.7":
        default_pylint_options += """\
--score=no\
    """.split('\n')

    return default_pylint_options

our_exit_code = 0

def executePyLint(filenames, show_todos, verbose):
    if verbose:
        print("Checking", filenames, "...")

    pylint_options = getOptions()
    if not show_todos:
        pylint_options.append("--notes=")

    # This is kind of a singleton module, pylint: disable=global-statement
    global our_exit_code

    def hasPyLintBugTrigger(filename):
        if pylint_version < "1.7":
            return False

        return os.path.basename(filename) in "ReformulationContractionExpressions.py"

    filenames = [
        filename
        for filename in
        filenames
        if not hasPyLintBugTrigger(filename)
    ]

    extra_options = os.environ.get("PYLINT_EXTRA_OPTIONS", "").split()
    if "" in extra_options:
        extra_options.remove("")
    command = ["pylint"] + pylint_options + extra_options + filenames

    process = subprocess.Popen(
        args   = command,
        stdout = subprocess.PIPE,
        stderr = subprocess.STDOUT,
        shell  = False
    )

    stdout, stderr = process.communicate()
    _exit_code = process.returncode

    assert not stderr, stderr

    if stdout:
        stdout = stdout.replace("\r\n", '\n')

        # Remove hard to disable error line given under Windows.
        lines = stdout.split(b"\n")
        try:
            error_line = lines.index(
                b"No config file found, using default configuration"
            )
            del lines[error_line]
            del lines[error_line]
        except ValueError:
            pass

        lines = [
            line.decode()
            for line in
            lines
        ]

        lines = [
            line
            for line in
            lines
            if "Unable to import 'resource'" not in line
        ]

        # If we filtered everything away, remove the leading file name report.
        if len(lines) == 1:
            assert lines[0].startswith("*****")
            lines = []

        for line in lines:
            print(line)

        if lines:
            our_exit_code = 1

    sys.stdout.flush()
