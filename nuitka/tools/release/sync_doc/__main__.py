#!/usr/bin/python
#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

""" Release tool to sync Developer Manual with code comments. """

import inspect
import re
import sys

from nuitka.utils.FileOperations import getFileContentByLine


def main():
    quote_start_re = re.compile("[Qq]uoting the ``(.*)`` documentation")
    quote_end_re = re.compile("(End|end) quoting the ``(.*)`` documentation")

    quoting = False

    for line in getFileContentByLine("Developer_Manual.rst"):
        if not quoting:
            print(line, end="")

        if not quoting:
            match = quote_start_re.search(line)

            if match:
                quoting = match.group(1)

                if "." in quoting:
                    import_from, import_value = quoting.rsplit(".", 1)

                    # Hopefully OK for us, pylint: disable=W0122
                    exec("from %s import %s" % (import_from, import_value))
                    item = getattr(sys.modules[import_from], import_value)

                    # Should potentially be derived from quoting line.
                    indentation = " " * line.find("Quoting")

                    # Empty line to separate
                    print()

                    for quote_line in inspect.getdoc(item).splitlines():
                        if quote_line:
                            print(indentation + quote_line)
                        else:
                            print()

                    print()
                else:
                    assert False, quoting

        if quoting:
            match = quote_end_re.search(line)

            if match:
                assert quoting == match.group(1)
                quoting = False

                print(line, end="")

    if quoting:
        sys.exit("Error, waiting for end of quote for %s failed" % quoting)


if __name__ == "__main__":
    main()
