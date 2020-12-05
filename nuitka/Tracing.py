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
from contextlib import contextmanager

from nuitka.utils.ThreadedExecutor import RLock

# Written by Options module.
is_quiet = False


def printIndented(level, *what):
    print("    " * level, *what)


def printSeparator(level=0):
    print("    " * level, "*" * 10)


def printLine(*what):
    print(*what)


def printError(message):
    print(message, file=sys.stderr)


def flushStandardOutputs():
    sys.stdout.flush()
    sys.stderr.flush()


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


# Locking seems necessary to avoid colored output split up.
trace_lock = RLock()


@contextmanager
def withTraceLock():
    """ Hold a lock, so traces cannot be output at the same time mixing them up. """

    trace_lock.acquire()
    yield
    trace_lock.release()


def my_print(*args, **kwargs):
    """Make sure we flush after every print.

    Not even the "-u" option does more than that and this is easy enough.

    Use kwarg style=[option] to print in a style listed below
    """
    with withTraceLock():
        if "style" in kwargs:
            style = kwargs["style"]
            del kwargs["style"]

            if "end" in kwargs:
                end = kwargs["end"]
                del kwargs["end"]
            else:
                end = "\n"

            if style is not None and sys.stdout.isatty():
                enable_style = getEnableStyleCode(style)

                if enable_style is None:
                    raise ValueError(
                        "%r is an invalid value for keyword argument style" % style
                    )

                _enableAnsi()

                print(enable_style, end="", **kwargs)

            print(*args, end=end, **kwargs)

            if style is not None and sys.stdout.isatty():
                print(getDisableStyleCode(), end="", **kwargs)
        else:
            print(*args, **kwargs)

        # Flush the output.
        kwargs.get("file", sys.stdout).flush()


# TODO: Stop using logging at all, and only OurLogger.
logging.basicConfig(format="Nuitka:%(levelname)s:%(message)s")


class OurLogger(object):
    def __init__(self, name, base_style=None):
        self.name = name
        self.base_style = base_style

    def my_print(self, message, **kwargs):
        # For overload, pylint: disable=no-self-use
        my_print(message, **kwargs)

    def warning(self, message, style="red"):
        message = "%s:WARNING: %s" % (self.name, message)

        style = style or self.base_style
        self.my_print(message, style=style, file=sys.stderr)

    def info(self, message, style=None):
        if not is_quiet:
            if self.name:
                message = "%s:INFO: %s" % (self.name, message)

            style = style or self.base_style
            self.my_print(message, style=style)


class FileLogger(OurLogger):
    def __init__(self, name, base_style=None, file_handle=sys.stdout):
        OurLogger.__init__(self, name=name, base_style=base_style)

        self.file_handle = file_handle

    def my_print(self, message, **kwargs):
        message = message + "\n"

        self.file_handle.write(message)
        self.file_handle.flush()

    def setFileHandle(self, file_handle):
        self.file_handle = file_handle

    def info(self, message, style=None):
        if not is_quiet or self.file_handle is not sys.stdout:
            message = "%s:INFO: %s" % (self.name, message)

            style = style or self.base_style
            self.my_print(message, style=style)

    def debug(self, message, style=None):
        if self.file_handle is not sys.stdout:
            message = "%s:DEBUG: %s" % (self.name, message)

            style = style or self.base_style
            self.my_print(message, style=style)


general = OurLogger("Nuitka")
codegen_missing = OurLogger("Nuitka-codegen-missing")
plugins_logger = OurLogger("Nuitka-Plugins")
recursion_logger = OurLogger("Nuitka-Recursion")
progress_logger = OurLogger("Nuitka-Progress")
memory_logger = OurLogger("Nuitka-Memory")
dependencies_logger = OurLogger("Nuitka-Dependencies")
optimization_logger = FileLogger("Nuitka-Optimization")
codegen_logger = OurLogger("Nuitka-Codegen")
inclusion_logger = FileLogger("Nuitka-Inclusion")
scons_logger = OurLogger("Nuitka-Scons")
postprocessing_logger = OurLogger("Nuitka-Postprocessing")
