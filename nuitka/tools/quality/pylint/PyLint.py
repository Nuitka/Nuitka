#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" PyLint handling for Nuitka.

Our usage of PyLint also works around a few issues that PyLint
has.

"""

import os
import sys

from nuitka.tools.testing.Common import hasModule, my_print
from nuitka.utils.Execution import check_output, executeProcess, getNullOutput

_pylint_version = None


def checkVersion():
    # pylint: disable=global-statement
    global _pylint_version

    if not hasModule("pylint"):
        sys.exit(
            "Error, pylint is not installed for this interpreter '%s' version."
            % os.environ["PYTHON"]
        )

    if _pylint_version is None:
        _pylint_version = check_output(
            [os.environ["PYTHON"], "-m", "pylint", "--version"], stderr=getNullOutput()
        )

        if str is not bytes:
            _pylint_version = _pylint_version.decode("utf8")

        _pylint_version = _pylint_version.split("\n")[0].split()[-1].strip(",")

    my_print("Using PyLint version:", _pylint_version)

    return tuple(int(d) for d in _pylint_version.split("."))


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
# bad-whitespace: No space allowed...
# Our spaces before keyword argument calls are not allowed, and this is
# not possible to distinguish.
#
# bad-continuation: Wrong hanging line indentation
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
# W1504: Using type() instead of isinstance() for typechecking.
# Nuitka is all about exact type checks, so this doesn't apply
#
# C0123: Using type() instead of isinstance() for typechecking.
# Nuitka is all about exact type checks, so this doesn't apply
#
# C0413: Import "..." should be placed at the top of the module
# There is no harm to this and imports are deal with by isort binary.
#
# C0411: external import "external" comes before "local"
# There is no harm to this and imports are deal with by "isort" binary.
#
# R0204: Redefinition of var type from x to y
# We do this all the time, e.g. to convert "str" to "unicode", or "list" to "str".
#
# R1705: Unnecessary "else" after "return"
# Frequently we use multiple branches where each returns.
#
# inconsistent-return-statements
# This makes no sense, having to have a variable for return is bad in my mind.
#
# c-extension-no-member
# Not too useful for us.
#
# useless-object-inheritance
# The code is for Python2 still, where it makes a difference, if you do
# not specify a base class, object is not the default there, but old style
# classes are, which perform different/worse.
#
# useless-return
# We like explicit None returns where the return value can be overloaded
# to something else, or the function is used along others that do return
# other things.
#
# ungrouped-imports
# We let isort do its thing most of the time, and where not, it's good
# enough for us to handle it manually.
#
# assignment-from-no-return
# assignment-from-none
# Overloaded functions are not detected, default value returns are all
# warned about, not worth it.
#
# raise-missing-from
# cannot do that, as long as we are backwards compatible

# import-outside-toplevel
# We do this deliberately, to avoid importing modules we do not use in
# all cases, e.g. Windows/macOS specific stuff.

# consider-using-f-string
# We need to be backward compatible for Python versions that do not have
# it.

# super-with-arguments
# Keeping code portable to Python2 is still good.

# consider-using-dict-comprehension
# Keeping code portable to Python2 is still good.

# unnecessary-lambda-assignment
# For deciders, we do this and like it.

# unnecessary-dunder-call
# We do make those intentionally only.

# arguments-differ
# We override static methods with non-static all the time.


def getOptions():
    pylint_version = checkVersion()

    # spell-checker: ignore setrecursionlimit,rcfile

    default_pylint_options = """\
--init-hook=import sys;sys.setrecursionlimit(1024*sys.getrecursionlimit())
--disable=I0011,E1103,W0632,\
C0123,C0411,C0413,cyclic-import,duplicate-code,\
deprecated-module,deprecated-method,deprecated-argument,assignment-from-none,\
ungrouped-imports,no-else-return,c-extension-no-member,\
inconsistent-return-statements,raise-missing-from,import-outside-toplevel,\
useless-object-inheritance,useless-return,assignment-from-no-return,\
redundant-u-string-prefix,consider-using-f-string,consider-using-dict-comprehension,
--enable=useless-suppression
--msg-template="{path}:{line} {msg_id} {symbol} {obj} {msg}"
--reports=no
--persistent=no
--method-rgx=[a-z_][a-zA-Z0-9_]{2,55}$
--module-rgx=.*
--function-rgx=.*
--variable-rgx=.*
--argument-rgx=.*
--dummy-variables-rgx=_.*|trace_collection
--ignored-argument-names=_.*|trace_collection
--const-rgx=.*
--max-line-length=125
--no-docstring-rgx=.*
--max-module-lines=6000
--min-public-methods=0
--max-public-methods=100
--max-args=11
--max-parents=14
--max-statements=50
--max-nested-blocks=10
--max-bool-expr=10
--score=no\
""".split(
        "\n"
    )

    if os.name != "nt":
        default_pylint_options.append("--rcfile=%s" % os.devnull)

    if pylint_version < (2, 17):
        default_pylint_options.append("--disable=bad-whitespace")
        default_pylint_options.append("--disable=bad-continuation")
        default_pylint_options.append("--disable=no-init")
        default_pylint_options.append("--disable=similar-code")
        default_pylint_options.append("--disable=I0012")
        default_pylint_options.append("--disable=W1504")
        default_pylint_options.append("--disable=R0204")
    else:
        default_pylint_options.append("--load-plugins=pylint.extensions.no_self_use")
        default_pylint_options.append("--disable=unnecessary-lambda-assignment")
        default_pylint_options.append("--disable=unnecessary-dunder-call")
        default_pylint_options.append("--disable=arguments-differ")
        default_pylint_options.append("--disable=redefined-slots-in-subclass")

    return default_pylint_options


our_exit_code = 0


def _cleanupPylintOutput(output):
    if str is not bytes:
        output = output.decode("utf8")

    # Normalize from Windows newlines potentially
    output = output.replace("\r\n", "\n")

    lines = [
        line
        for line in output.split("\n")
        if line
        if "Using config file" not in line
        if "Unable to import 'resource'" not in line
        if "Bad option value 'self-assigning-variable'" not in line
    ]

    try:
        error_line = lines.index("No config file found, using default configuration")
        del lines[error_line]

        if error_line < len(lines):
            del lines[error_line]
    except ValueError:
        pass

    return lines


def _executePylint(filenames, pylint_options, extra_options):
    # This is kind of a singleton module, pylint: disable=global-statement
    global our_exit_code

    command = (
        [os.environ["PYTHON"], "-m", "pylint"]
        + pylint_options
        + extra_options
        + filenames
    )

    stdout, stderr, exit_code = executeProcess(command)

    if exit_code == -11:
        sys.exit("Error, segfault from pylint.")

    stdout = _cleanupPylintOutput(stdout)
    stderr = _cleanupPylintOutput(stderr)

    if stderr:
        our_exit_code = 1

        for line in stderr:
            my_print(line)

    if stdout:
        # If we filtered everything away, remove the leading file name reports.
        while stdout and stdout[-1].startswith("******"):
            del stdout[-1]

        for line in stdout:
            my_print(line)

        if stdout:
            our_exit_code = 1

    sys.stdout.flush()


def hasPyLintBugTrigger(filename):
    """Decide if a filename should be skipped."""
    # Currently everything is good, but it's a useful hook, pylint_: disable=unused-argument
    if filename == "nuitka/distutils/Build.py":
        return True

    return False


def isSpecificPythonOnly(filename):
    """Decide if something is not used for this specific Python."""

    # Currently everything is portable, but it's a useful hook, pylint: disable=unused-argument
    return False


def executePyLint(filenames, show_todo, verbose, one_by_one):
    filenames = list(filenames)

    if verbose:
        my_print("Checking", filenames, "...")

    pylint_options = getOptions()
    if not show_todo:
        pylint_options.append("--notes=")

    filenames = [
        filename
        for filename in filenames
        if not hasPyLintBugTrigger(filename)
        if not isSpecificPythonOnly(filename)
    ]

    extra_options = os.getenv("PYLINT_EXTRA_OPTIONS", "").split()
    if "" in extra_options:
        extra_options.remove("")

    if one_by_one:
        for filename in filenames:
            my_print("Checking", filename, ":")
            _executePylint([filename], pylint_options, extra_options)
    else:
        _executePylint(filenames, pylint_options, extra_options)


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
