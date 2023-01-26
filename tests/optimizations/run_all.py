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

from nuitka.tools.testing.Common import (
    convertUsing2to3,
    createSearchMode,
    decideFilenameVersionSkip,
    getPythonSysPath,
    my_print,
    setup,
    withPythonPathChange,
)
from nuitka.TreeXML import toString
from nuitka.utils.Execution import check_call
from nuitka.utils.FileOperations import getFileContents

python_version = setup(suite="optimizations")

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
        "ImportModuleNameHardExists",
        "ImportModuleNameHardMaybeExists",
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

        if kind == "FrameModule":
            checkSequence(filename, getRole(statement, "statements"))

            continue

        if kind == "FrameFunction":
            checkSequence(filename, getRole(statement, "statements"))

            continue

        if kind.startswith("AssignmentVariable"):
            variable_name = statement.attrib["variable_name"]

            # Ignore "__spec__" assignment for Python3.4, it is not going
            # to be static.
            if variable_name == "__spec__":
                continue

            (assign_source,) = getRole(statement, "source")

            if getKind(assign_source) in ("FunctionCreation", "FunctionCreationOld"):
                continue

            if not isConstantExpression(assign_source):
                search_mode.onErrorDetected(
                    "%s: Error, assignment from non-constant '%s'."
                    % (getSourceRef(filename, statement), getKind(assign_source))
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
    # Complex stuff, pylint: disable=too-many-branches,too-many-statements

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

            xml_filename = filename.replace(".py", ".xml")

            command = [
                os.environ["PYTHON"],
                os.path.abspath(os.path.join("..", "..", "bin", "nuitka")),
                "--xml=%s" % xml_filename,
                "--quiet",
                "--module",
                "--nofollow-imports",
                "--generate-c-only",
                "--no-progressbar",
                filename,
            ]

            if search_mode.isCoverage():
                # To avoid re-execution, which is not acceptable to coverage.
                if "PYTHONHASHSEED" not in os.environ:
                    os.environ["PYTHONHASHSEED"] = "0"

                command.insert(2, "--must-not-re-execute")

                command = (
                    command[0:1]
                    + ["-S", "-m", "coverage", "run", "--rcfile", os.devnull, "-a"]
                    + command[1:]
                )

                # Coverage modules hates Nuitka to re-execute, and so we must avoid
                # that.
                python_path = getPythonSysPath()
            else:
                python_path = None

            with withPythonPathChange(python_path):
                check_call(command)

            # Parse the result into XML and check it
            result = getFileContents(xml_filename)
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
                my_print("Optimization result:")
                my_print(result, style="test-debug")
                my_print("FAIL.", style="red")

                raise

            my_print("OK.")

    search_mode.finish()


if __name__ == "__main__":
    main()
