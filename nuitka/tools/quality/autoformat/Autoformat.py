#!/usr/bin/env python
#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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

""" Tool to automatically format source code in Nuitka style.

"""

import os
import re
import shutil

from nuitka.Tracing import my_print


def cleanupWindowsNewlines(filename):
    """ Remove Windows new-lines from a file.

        Simple enough to not depend on external binary.
    """

    source_code = open(filename, "rb").read()

    updated_code = source_code.replace(b"\r\n", b"\n")
    updated_code = updated_code.replace(b"\n\r", b"\n")

    if updated_code != source_code:
        my_print("Fixing Windows new lines for", filename)

        with open(filename, "wb") as out_file:
            out_file.write(updated_code)


def _updateCommentNode(comment_node):
    if "pylint:" in str(comment_node.value):

        def replacer(part):
            def renamer(pylint_token):
                # pylint: disable=too-many-branches,too-many-return-statements
                if pylint_token == "E0602":
                    return "undefined-variable"
                elif pylint_token in ("E0401", "F0401"):
                    return "import-error"
                elif pylint_token == "E1102":
                    return "not-callable"
                elif pylint_token == "E1133":
                    return "  not-an-iterable"
                elif pylint_token == "E1128":
                    return "assignment-from-none"
                # Save line length for this until isort is better at long lines.
                elif pylint_token == "useless-suppression":
                    return "I0021"
                #                     elif pylint_token == "I0021":
                #                        return "useless-suppression"
                elif pylint_token == "R0911":
                    return "too-many-return-statements"
                elif pylint_token == "R0201":
                    return "no-self-use"
                elif pylint_token == "R0902":
                    return "too-many-instance-attributes"
                elif pylint_token == "R0912":
                    return "too-many-branches"
                elif pylint_token == "R0914":
                    return "too-many-locals"
                elif pylint_token == "R0915":
                    return "too-many-statements"
                elif pylint_token == "W0123":
                    return "eval-used"
                elif pylint_token == "W0603":
                    return "global-statement"
                elif pylint_token == "W0613":
                    return "unused-argument"
                elif pylint_token == "W0622":
                    return "redefined-builtin"
                elif pylint_token == "W0703":
                    return "broad-except"
                else:
                    return pylint_token

            return part.group(1) + ",".join(
                sorted(renamer(token) for token in part.group(2).split(","))
            )

        new_value = re.sub(
            r"(pylint\: disable=)(.*)", replacer, str(comment_node.value), flags=re.M
        )
        comment_node.value = new_value


def autoformat(filename, abort=False):
    from baron.parser import (  # pylint: disable=I0021,import-error,no-name-in-module
        ParsingError,  # @UnresolvedImport
    )
    from redbaron import (  # pylint: disable=I0021,import-error,no-name-in-module
        RedBaron,  # @UnresolvedImport
    )

    my_print("Consider", filename, end=": ")

    old_code = open(filename, "r").read()

    try:
        red = RedBaron(old_code)
        # red = RedBaron(old_code.rstrip()+'\n')
    except ParsingError:
        if abort:
            raise

        my_print("PARSING ERROR.")
        return 2

    for node in red.find_all("CommentNode"):
        try:
            _updateCommentNode(node)
        except Exception:
            my_print("Problem with", node)
            node.help(deep=True, with_formatting=True)
            raise

    new_code = red.dumps()

    if new_code != old_code:
        new_name = filename + ".new"

        with open(new_name, "w") as source_code:
            source_code.write(red.dumps())

        if os.name == "nt":
            cleanupWindowsNewlines(new_name)

        # There is no way to safely replace a file on Windows, but lets try on Linux
        # at least.
        old_stat = os.stat(filename)

        try:
            os.rename(new_name, filename)
        except OSError:
            shutil.copyfile(new_name, filename)
            os.unlink(new_name)

        os.chmod(filename, old_stat.st_mode)

        my_print("updated.")
        changed = 1
    else:
        my_print("OK.")
        changed = 0

    return changed
