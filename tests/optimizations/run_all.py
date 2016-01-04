#!/usr/bin/env python
#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

import os, sys, subprocess

# The test runner needs "lxml" itself.
try:
    import lxml.etree
except ImportError:
    print("Warning, no 'lxml' module installed, cannot do XML based tests.")
    sys.exit(0)

# Find common code relative in file system. Not using packages for test stuff.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            ".."
        )
    )
)
from test_common import (
    my_print,
    setup,
    convertUsing2to3,
    createSearchMode,
    hasModule,
    check_output
)

python_version = setup()

# The Python version used by Nuitka needs "lxml" too.
if not hasModule("lxml.etree"):
    print("Warning, no 'lxml' module installed, cannot run XML based tests.")
    sys.exit(0)

search_mode = createSearchMode()

def getKind(node):
    result = node.attrib[ "kind" ]

    result = result.replace("Statements", "")
    result = result.replace("Statement", "")
    result = result.replace("Expression", "")

    return result

def getRole(node, role):
    for child in node:
        if child.tag == "role" and child.attrib["name"] == role:
            return child
    else:
        return None

def getSourceRef(node):
    return "%s:%s" % (
        filename,
        node.attrib["line"]
    )

def checkSequence(statements):
    for statement in statements:
        kind = getKind(statement)

        # Printing is fine.
        if kind == "PrintValue":
            print_arg, = getRole(statement, "value")

            if getKind(print_arg) not in ("ConstantRef",
                                          "ModuleFileAttributeRef"):
                sys.exit(
                    "%s: Error, print of non-constant %s." % (
                        getSourceRef(statement),
                        getKind(print_arg)
                    )
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

        if kind == "Frame":
            checkSequence(getRole(statement, "statements"))

            continue

        if kind == "AssignmentVariable":
            assign_source, = getRole(statement, "source")

            source_kind = getKind(assign_source)

            if source_kind not in("ConstantRef",
                                  "ImportModuleHard",
                                  "ModuleFileAttributeRef"):
                sys.exit("Error, assignment from of non-constant %s." % source_kind)
            continue

        print(lxml.etree.tostring(statement, pretty_print = True))

        sys.exit("Error, non-print statement of unknown kind '%s'." % kind)


for filename in sorted(os.listdir('.')):
    if not filename.endswith(".py") or filename.startswith("run_"):
        continue

    active = search_mode.consider(
        dirname  = None,
        filename = filename
    )

    extra_flags = ["expect_success"]

    if active:
        # Apply 2to3 conversion if necessary.
        if python_version.startswith('3'):
            filename, changed = convertUsing2to3(filename)
        else:
            changed = False

        my_print("Consider", filename, end = ' ')

        command = [
            os.environ["PYTHON"],
            os.path.abspath(os.path.join("..", "..", "bin", "nuitka")),
            "--dump-xml",
            "--module",
            filename
        ]


        if search_mode.isCoverage():
            # To avoid re-execution, which is not acceptable to coverage.
            if "PYTHONHASHSEED" not in os.environ:
                os.environ["PYTHONHASHSEED"] = '0'

            # Coverage modules hates Nuitka to re-execute, and so we must avoid
            # that.
            python_path = subprocess.check_output(
                [
                    os.environ["PYTHON"],
                    "-c"
                    "import sys, os; print(os.pathsep.join(sys.path))"
                ]
            )

            if sys.version_info >= (3,):
                python_path = python_path.decode("utf8")

            os.environ["PYTHONPATH"] = python_path.strip()


            command.insert(2, "--must-not-re-execute")

            command = command[0:1] + [
                "-S",
                "-m",
                "coverage",
                "run",
                "--rcfile", os.devnull,
                "-a",
            ] + command[1:]

        result = check_output(
            command
        )

        # Parse the result into XML and check it.
        root = lxml.etree.fromstring(result)
        module_body = root[0]
        module_statements_sequence = module_body[0]

        assert len(module_statements_sequence) == 1
        module_statements = next(iter(module_statements_sequence))

        checkSequence(module_statements)

        if changed:
            os.unlink(filename)

        my_print("OK.")
    else:
        my_print("Skipping", filename)

search_mode.finish()
