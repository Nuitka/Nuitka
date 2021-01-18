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

""" Test runners test

This shows that known good existing static optimization works and produces
constant results. This should be used to preserve successful optimization
at compile time against later changes breaking them undetected.

"""

from __future__ import print_function

import os
import sys

# The test runner needs "lxml" itself.
try:
    import lxml.etree
except ImportError:
    print("Warning, no 'lxml' module installed, cannot do XML based tests.")
    sys.exit(0)

# Find nuitka package relative to us.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    ),
)

# isort:start
from nuitka.TreeXML import toString

from nuitka.tools.testing.Common import (  # isort:skip
    check_output,
    convertUsing2to3,
    createSearchMode,
    decideFilenameVersionSkip,
    my_print,
    setup,
)

python_version = setup()

search_mode = createSearchMode()


def getKind(node):
    result = node.attrib["kind"]

    result = result.replace("Statements", "")
    result = result.replace("Statement", "")
    result = result.replace("Expression", "")

    return result


def getRole(node, role):
    for child in node:
        if child.tag == "role" and child.attrib["name"] == role:
            return child
    return None


def getSourceRef(filename, node):
    return "%s:%s" % (filename, node.attrib["line"])


def isConstantExpression(expression):
    kind = getKind(expression)

    return kind.startswith("Constant") or kind in (
        "ImportModuleHard",
        "ImportName",
        "ModuleAttributeFileRef",
        "ModuleLoaderRef",
    )


def checkSequence(filename, statements):
    # Complex stuff, pylint: disable=too-many-branches

    for statement in statements:
        kind = getKind(statement)

        # Printing is fine.
        if kind == "PrintValue":
            (print_arg,) = getRole(statement, "value")

            if not isConstantExpression(print_arg):
                search_mode.onErrorDetected(
                    "%s: Error, print of non-constant '%s'."
                    % (getSourceRef(filename, statement), getKind(print_arg))
                )

            continue

        if kind == "PrintNewline":
            continue

        # Printing in Python3 is a function call whose return value is ignored.
        if kind == "Only":
            only_expression = getRole(statement, "expression")[0]

            if getKind(only_expression) == "CallNoKeywords":
                called_expression = getRole(only_expression, "called")[0]

                if getKind(called_expression) == "BuiltinRef":
                    if called_expression.attrib["builtin_name"] == "print":
                        continue

        # Trying of printing is fine, but not needed
        if kind == "Try" and False:
            tried = getRole(statement, "tried")

            checkSequence(filename, getRole(tried[0], "statements"))

            continue

        if kind == "FrameModule":
            checkSequence(filename, getRole(statement, "statements"))

            continue

        if kind == "FrameFunction":
            checkSequence(filename, getRole(statement, "statements"))

            continue

        if kind == "AssignmentVariable":
            variable_name = statement.attrib["variable_name"]

            # Ignore "__spec__" assignment for Python3.4, it is not going
            # to be static.
            if variable_name == "__spec__":
                continue

            (assign_source,) = getRole(statement, "source")

            if getKind(assign_source) == "FunctionCreation":
                continue

            if not isConstantExpression(assign_source):
                search_mode.onErrorDetected(
                    "Error, assignment from non-constant '%s'." % getKind(assign_source)
                )

            continue

        if kind == "AssignmentAttribute":
            (assign_source,) = getRole(statement, "expression")

            if getKind(assign_source) == "ModuleAttributeSpecRef":
                continue

            search_mode.onErrorDetected(
                "Error, attribute assignment to '%s'." % getKind(assign_source)
            )

        if kind in ("ReturnNone", "ReturnConstant"):
            continue

        print(toString(statement))
        search_mode.onErrorDetected(
            "Error, non-print statement of unknown kind '%s'." % kind
        )


def main():
    # Complex stuff, pylint: disable=too-many-branches

    for filename in sorted(os.listdir(".")):
        if not filename.endswith(".py") or filename.startswith("run_"):
            continue

        if not decideFilenameVersionSkip(filename):
            continue

        active = search_mode.consider(dirname=None, filename=filename)

        if active:
            # Apply 2to3 conversion if necessary.
            if python_version >= (3,):
                filename, changed = convertUsing2to3(filename)
            else:
                changed = False

            my_print("Consider", filename, end=" ")

            command = [
                os.environ["PYTHON"],
                os.path.abspath(os.path.join("..", "..", "bin", "nuitka")),
                "--xml",
                "--quiet",
                "--module",
                filename,
            ]

            if search_mode.isCoverage():
                # To avoid re-execution, which is not acceptable to coverage.
                if "PYTHONHASHSEED" not in os.environ:
                    os.environ["PYTHONHASHSEED"] = "0"

                # Coverage modules hates Nuitka to re-execute, and so we must avoid
                # that.
                python_path = check_output(
                    [
                        os.environ["PYTHON"],
                        "-c",
                        "import sys, os; print(os.pathsep.join(sys.path))",
                    ]
                )

                if sys.version_info >= (3,):
                    python_path = python_path.decode("utf8")

                os.environ["PYTHONPATH"] = python_path.strip()

                command.insert(2, "--must-not-re-execute")

                command = (
                    command[0:1]
                    + ["-S", "-m", "coverage", "run", "--rcfile", os.devnull, "-a"]
                    + command[1:]
                )

            result = check_output(command)

            # Parse the result into XML and check it.
            try:
                root = lxml.etree.fromstring(result)
            except lxml.etree.XMLSyntaxError:
                my_print("Problematic XML output:")
                my_print(result)
                raise

            module_body = root[0]
            module_statements_sequence = module_body[0]

            assert len(module_statements_sequence) == 1
            module_statements = next(iter(module_statements_sequence))

            try:
                checkSequence(filename, module_statements)

                for function in root.xpath('role[@name="functions"]/node'):
                    (function_body,) = function.xpath('role[@name="body"]')
                    function_statements_sequence = function_body[0]
                    assert len(function_statements_sequence) == 1
                    function_statements = next(iter(function_statements_sequence))

                    checkSequence(filename, function_statements)

                if changed:
                    os.unlink(filename)
            except SystemExit:
                my_print("FAIL.")
                raise

            my_print("OK.")

            if search_mode.abortIfExecuted():
                break

    search_mode.finish()


if __name__ == "__main__":
    main()
