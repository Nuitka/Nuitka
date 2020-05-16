#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Outputs to the user.

Printing with intends or plain, mostly a compensation for the print strangeness.

We want to avoid "from __future__ import print_function" in every file out
there, which makes adding another debug print rather tedious. This should
cover all calls/uses of "print" we have to do, and the make it easy to simply
to "print for_debug" without much hassle (braces).

"""

from __future__ import print_function

import logging
import os
import sys


def printIndented(level, *what):
    print("    " * level, *what)


def printSeparator(level=0):
    print("    " * level, "*" * 10)


def printLine(*what):
    print(*what)


def printError(message):
    print(message, file=sys.stderr)


def flushStdout():
    sys.stdout.flush()


def getEnableStyleCode(style):
    if style == "pink":
        style = "\033[95m"
    elif style == "blue":
        style = "\033[94m"
    elif style == "green":
        style = "\033[92m"
    elif style == "yellow":
        style = "\033[93m"
    elif style == "red":
        style = "\033[91m"
    elif style == "bold":
        style = "\033[1m"
    elif style == "underline":
        style = "\033[4m"
    else:
        style = None

    return style


_enabled_ansi = False


def _enableAnsi():
    # singleton, pylint: disable=global-statement
    global _enabled_ansi
    if not _enabled_ansi:

        # Only necessary on Windows, as a side effect of this, ANSI colors get enabled
        # for the terminal and never deactivated, so we are free to use them after
        # this.
        if os.name == "nt":
            os.system("")

        _enabled_ansi = True


def getDisableStyleCode():
    return "\033[0m"


def my_print(*args, **kwargs):
    """ Make sure we flush after every print.

    Not even the "-u" option does more than that and this is easy enough.

    Use kwarg style=[option] to print in a style listed below
    """

    if "style" in kwargs:
        style = kwargs["style"]
        del kwargs["style"]

        if style is not None and sys.stdout.isatty():
            enable_style = getEnableStyleCode(style)

            if enable_style is None:
                raise ValueError(
                    "%r is an invalid value for keyword argument style" % style
                )

            _enableAnsi()

            print(enable_style, end="")

        print(*args, **kwargs)

        if style is not None and sys.stdout.isatty():
            print(getDisableStyleCode(), end="")
    else:
        print(*args, **kwargs)

    flushStdout()


# TODO: Stop using logging at all, and only OurLogger.
logging.basicConfig(format="Nuitka:%(levelname)s:%(message)s")


class OurLogger(object):
    def __init__(self, name, base_style=None):
        self.name = name
        self.base_style = base_style

    def warning(self, message, style="red"):
        message = "%s:WARNING: %s" % (self.name, message)

        style = style or self.base_style
        my_print(message, style=style)

    def info(self, message, style=None):
        message = "%s:INFO: %s" % (self.name, message)

        style = style or self.base_style
        my_print(message, style=style)


general = OurLogger("Nuitka")
codegen_missing = OurLogger("Nuitka-codegen-missing")
plugins_logger = OurLogger("Nuitka-Plugins")
recursion_logger = OurLogger("Nuitka-Recursion")
dependencies_logger = OurLogger("Nuitka-Dependencies")
