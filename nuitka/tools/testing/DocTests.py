#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Handling of "doctest" tests to be converted to actual Python code.

That makes sense, because we want to compile and compare it as a
script and not an in memory bytecode.
"""

import ast
import sys

from .Common import indentedCode


def convertToPython(doc_tests, line_filter=None):
    """Convert give doctest string to static Python code."""
    # This is convoluted, but it just needs to work, pylint: disable=too-many-branches

    import doctest

    code = doctest.script_from_examples(doc_tests)

    if code.endswith("\n"):
        code += "#\n"
    else:
        assert False

    output = []
    inside = False

    def getPrintPrefixed(evaluated, line_number):
        try:
            node = ast.parse(evaluated.lstrip(), "eval")
        except SyntaxError:
            return evaluated

        if node.body[0].__class__.__name__ == "Expr":
            count = 0

            while evaluated.startswith(" " * count):
                count += 1

            if sys.version_info < (3,):
                modified = (count - 1) * " " + "print " + evaluated
                return (
                    (count - 1) * " "
                    + ("print 'Line %d'" % line_number)
                    + "\n"
                    + modified
                )
            else:
                modified = (count - 1) * " " + "print(" + evaluated + "\n)\n"
                return (
                    (count - 1) * " "
                    + ("print('Line %d'" % line_number)
                    + ")\n"
                    + modified
                )
        else:
            return evaluated

    def getTried(evaluated, line_number):
        if sys.version_info < (3,):
            return """
try:
%(evaluated)s
except Exception as __e:
    print "Occurred", type(__e), __e
""" % {
                "evaluated": indentedCode(
                    getPrintPrefixed(evaluated, line_number).split("\n"), 4
                )
            }
        else:
            return """
try:
%(evaluated)s
except Exception as __e:
    print("Occurred", type(__e), __e)
""" % {
                "evaluated": indentedCode(
                    getPrintPrefixed(evaluated, line_number).split("\n"), 4
                )
            }

    def isOpener(evaluated):
        evaluated = evaluated.lstrip()

        if evaluated == "":
            return False

        return evaluated.split()[0] in (
            "def",
            "with",
            "class",
            "for",
            "while",
            "try:",
            "except",
            "except:",
            "finally:",
            "else:",
        )

    chunk = None
    for line_number, line in enumerate(code.split("\n")):
        # print "->", inside, line

        if line_filter is not None and line_filter(line):
            continue

        if inside and line and line[0].isalnum() and not isOpener(line):
            output.append(getTried("\n".join(chunk), line_number))

            chunk = []
            inside = False

        if inside and not (line.startswith("#") and line.find("SyntaxError:") != -1):
            chunk.append(line)
        elif line.startswith("#"):
            if line.find("SyntaxError:") != -1:
                # print "Syntax error detected"

                if inside:
                    # print "Dropping chunk", chunk

                    chunk = []
                    inside = False
                else:
                    del output[-1]
        elif isOpener(line):
            inside = True
            chunk = [line]
        elif line.strip() == "":
            output.append(line)
        else:
            output.append(getTried(line, line_number))

    return "\n".join(output).rstrip() + "\n"


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
