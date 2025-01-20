#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Outputs to the user.

Printing with intends or plain, mostly a compensation for the print strangeness.

We want to avoid "from __future__ import print_function" in every file out
there, which makes adding another debug print rather tedious. This should
cover all calls/uses of "print" we have to do, and the make it easy to simply
to "print for_debug" without much hassle (braces).

"""

from __future__ import print_function

import os
import struct
import sys
import textwrap
import traceback

from nuitka.__past__ import (  # pylint: disable=redefined-builtin
    BrokenPipeError,
    raw_input,
)
from nuitka.utils.Utils import isWin32Windows

# Written by Options module.
is_quiet = False

# We have to interact with displayed progress bars when doing out trace outputs.
progress = None


def setQuiet():
    # singleton, pylint: disable=global-statement
    global is_quiet
    is_quiet = True


def printIndented(level, *what):
    print("    " * level, *what)


def printSeparator(level=0):
    print("    " * level, "*" * 10)


def printLine(*what, **kwargs):
    is_atty = sys.stdout.isatty()

    if progress and is_atty:
        progress.close()

    print(*what, **kwargs)


def printError(message):
    my_print(message, file=sys.stderr)


def flushStandardOutputs():
    sys.stdout.flush()
    sys.stderr.flush()


def _getEnableStyleCode(style):
    style = _aliasStyle(style)

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


def hasTerminalLinkSupport():
    if not sys.stdout.isatty():
        return False

    terminal_name = os.getenv("TERM_PROGRAM")

    if terminal_name is not None:
        if terminal_name == "vscode":
            return True

    # Windows terminal, in some cases, but not on Windows 11 unfortunately there
    # is no difference between CMD with its own terminal and CMD in Windows
    # Terminal, not even parent processes.
    if isWin32Windows():
        if "WT_SESSION" in os.environ or "WT_PROFILE_ID" in os.environ:
            return True

    # Powershell, should be used in new terminals only. Also hard to detect,
    # although here we could search parent process names to determine it.
    if isWin32Windows():
        if "PSModulePath" in os.environ:
            return True

    return False


def formatTerminalLink(text, link):
    if link is not None and hasTerminalLinkSupport():
        return "\033]8;;%s\033\\%s\033]8;;\033\\" % (link, text)
    else:
        return text


def _getDisableStyleCode():
    return "\033[0m"


def _getIoctlGWINSZ(fd):
    # On non-Windows, this might work, # spell-checker: ignore GWINSZ,TIOCGWINSZ
    try:
        # pylint: disable=I0021,import-error
        import fcntl
        import termios

        return struct.unpack("hh", fcntl.ioctl(fd, termios.TIOCGWINSZ, "1234"))
    except BaseException:  # Catch all the things, pylint: disable=broad-except
        return None


def _getTerminalSizeWin32():
    try:
        from ctypes import create_string_buffer, windll

        # handles are -10 to -12
        h = windll.kernel32.GetStdHandle(-12)
        buffer = create_string_buffer(22)

        res = windll.kernel32.GetConsoleScreenBufferInfo(h, buffer)
        if res:
            # TODO: Could also define the C structure
            (
                _,
                _,
                _,
                _,
                _,
                left,
                top,
                right,
                bottom,
                _,
                _,
            ) = struct.unpack("hhhhHhhhhhh", buffer.raw)

            columns = right - left + 1
            lines = bottom - top + 1

            return lines, columns
    except BaseException:  # Catch all the things, pylint: disable=broad-except
        return None


def _getTerminalSize():
    # For Python2, we get to do it ourselves.

    if str is bytes:
        if isWin32Windows():
            columns = _getTerminalSizeWin32()
        else:
            # Try all file handles.
            columns = _getIoctlGWINSZ(0) or _getIoctlGWINSZ(1) or _getIoctlGWINSZ(2)

        if columns:
            return columns[1]

        try:
            return int(os.getenv("COLUMNS", "1000"))
        except ValueError:
            return 1000
    else:
        try:
            return os.get_terminal_size()[0]
        except OSError:
            return 1000


def _aliasStyle(style):
    """Map named styles to concrete colors."""

    # return driven, pylint: disable=too-many-return-statements

    if style == "test-prepare":
        return "pink"
    if style == "test-progress":
        return "blue"
    if style == "test-debug":
        return "bold"
    if style == "link":
        return "blue"
    if style == "warning":
        return "yellow"
    if style == "scons-unexpected":
        return "yellow"
    if style == "error":
        return "red"
    else:
        return style


def _my_print(file_output, is_atty, args, kwargs):
    try:
        if "style" in kwargs:
            style = kwargs["style"]
            del kwargs["style"]

            if "end" in kwargs:
                end = kwargs["end"]
                del kwargs["end"]
            else:
                end = "\n"

            if style is not None and is_atty:
                enable_style = _getEnableStyleCode(style)

                if enable_style is None:
                    raise ValueError(
                        "%r is an invalid value for keyword argument style" % style
                    )

                _enableAnsi()

                print(enable_style, end="", **kwargs)

            print(*args, end=end, **kwargs)

            if style is not None and is_atty:
                print(_getDisableStyleCode(), end="", **kwargs)
        else:
            print(*args, **kwargs)

        # Flush the output.
        file_output.flush()
    except BrokenPipeError:
        pass


def my_print(*args, **kwargs):
    """Make sure we flush after every print.

    Not even the "-u" option does more than that and this is easy enough.

    Use kwarg style=[option] to print in a style listed below
    """

    file_output = kwargs.get("file", sys.stdout)
    is_atty = file_output.isatty()

    if progress and is_atty:
        with progress.withExternalWritingPause():
            _my_print(file_output, is_atty, args, kwargs)
    else:
        _my_print(file_output, is_atty, args, kwargs)


class ReportingSystemExit(SystemExit):
    """Our own system exit, after which a report should be written."""

    def __init__(self, exit_code, exit_message):
        SystemExit.__init__(self, exit_code)

        self.exit_message = exit_message


class OurLogger(object):
    def __init__(self, name, quiet=False, base_style=None):
        self.name = name
        self.base_style = base_style
        self.is_quiet = quiet

    def my_print(self, message, **kwargs):
        # For overload, pylint: disable=no-self-use
        my_print(message, **kwargs)

    @staticmethod
    def _warnMnemonic(mnemonic, style, output_function):
        if mnemonic.startswith("http"):
            url = mnemonic
            extra_prefix = ""
        else:
            url = "https://nuitka.net/info/%s.html" % mnemonic
            extra_prefix = "Complex topic! "

        output_function(
            """    %sMore information can be found at %s%s"""
            % (extra_prefix, _getEnableStyleCode("link"), url),
            style=style,
        )

    def _printFormatted(self, prefix, message, style, keep_format):
        style = style or self.base_style

        if sys.stderr.isatty() and not keep_format:
            width = _getTerminalSize() or 10000
        else:
            width = 10000

        formatted_message = textwrap.fill(
            message,
            width=width,
            initial_indent=prefix,
            subsequent_indent=prefix,
            break_on_hyphens=False,
            break_long_words=False,
            expand_tabs=False,
            replace_whitespace=False,
        )
        self.my_print(formatted_message, style=style, file=sys.stderr)

    def warning(self, message, style="yellow", mnemonic=None, keep_format=False):
        if mnemonic is not None:
            from .Options import shallDisplayWarningMnemonic

            if not shallDisplayWarningMnemonic(mnemonic):
                return

        if self.name:
            prefix = "%s:WARNING: " % self.name
        else:
            prefix = "WARNING: "

        self._printFormatted(
            prefix=prefix, message=message, style=style, keep_format=keep_format
        )

        if mnemonic is not None:
            self._warnMnemonic(mnemonic, style=style, output_function=self.warning)

    def sysexit(
        self, message="", style=None, mnemonic=None, exit_code=1, reporting=False
    ):
        from nuitka.Progress import closeProgressBar

        closeProgressBar()

        if exit_code != 0 and style is None:
            style = "red"

        if message:
            if exit_code != 0:
                self.my_print(
                    "FATAL: %s" % message,
                    style=style,
                    file=sys.stderr,
                )
            else:
                self.my_print(
                    message,
                    style=style,
                    file=sys.stderr,
                )

        if mnemonic is not None:
            self._warnMnemonic(mnemonic, style=style, output_function=self.warning)

        if reporting:
            raise ReportingSystemExit(exit_code=exit_code, exit_message=message)

        sys.exit(exit_code)

    def sysexit_exception(self, message, exception, exit_code=1):
        self.my_print("FATAL: %s" % message, style="red", file=sys.stderr)

        traceback.print_exc()
        self.sysexit("FATAL:" + repr(exception), exit_code=exit_code, reporting=True)

    def isQuiet(self):
        return is_quiet or self.is_quiet

    def info(self, message, style=None, mnemonic=None, prefix=None, keep_format=False):
        if not self.isQuiet():
            self._printFormatted(
                prefix=(
                    "%s: " % self.name
                    if prefix is None
                    else "%s:%s: " % (self.name, prefix)
                ),
                message=message,
                style=style,
                keep_format=keep_format,
            )

            if mnemonic is not None:
                self._warnMnemonic(mnemonic, style=style, output_function=self.info)


class FileLogger(OurLogger):
    def __init__(self, name, quiet=False, base_style=None, file_handle=None):
        OurLogger.__init__(self, name=name, quiet=quiet, base_style=base_style)

        self.file_handle = file_handle

    def __del__(self):
        if self.file_handle is not None:
            self.file_handle.close()

    def my_print(self, message, **kwargs):
        if "file" not in kwargs:
            kwargs["file"] = self.file_handle or sys.stdout

        my_print(message, **kwargs)
        kwargs["file"].flush()

    def setFileHandle(self, file_handle):
        self.file_handle = file_handle

    def isFileOutput(self):
        return self.file_handle is not None

    def info(self, message, style=None, mnemonic=None):
        if not self.isQuiet() or self.file_handle:
            message = "%s: %s" % (self.name, message)

            style = style or self.base_style
            self.my_print(message, style=style)

            if mnemonic is not None:
                self._warnMnemonic(mnemonic, style=style, output_function=self.my_print)

    def debug(self, message, style=None):
        if self.file_handle:
            message = "%s:DEBUG: %s" % (self.name, message)

            style = style or self.base_style
            self.my_print(message, style=style)

    def info_to_file_only(self, message, style=None):
        if self.file_handle:
            self.info(message, style=style)

    def info_if_file(self, message, other_logger, style=None):
        if self.file_handle:
            self.info(message, style=style)
        else:
            other_logger.info(message, style=style)


general = OurLogger("Nuitka")
plugins_logger = OurLogger("Nuitka-Plugins")
recursion_logger = OurLogger("Nuitka-Inclusion")
progress_logger = OurLogger("Nuitka-Progress", quiet=True)
memory_logger = OurLogger("Nuitka-Memory")
metadata_logger = OurLogger("Nuitka-Metadata")
optimization_logger = FileLogger("Nuitka-Optimization")
pgo_logger = FileLogger("Nuitka-PGO")
code_generation_logger = OurLogger("Nuitka-CodeGen")
inclusion_logger = FileLogger("Nuitka-Inclusion")
scons_logger = OurLogger("Nuitka-Scons")
scons_details_logger = OurLogger("Nuitka-Scons")
postprocessing_logger = OurLogger("Nuitka-Postprocessing")
options_logger = OurLogger("Nuitka-Options")
unusual_logger = OurLogger("Nuitka-Unusual")
data_composer_logger = OurLogger("Nuitka-DataComposer")
onefile_logger = OurLogger("Nuitka-Onefile")
tools_logger = OurLogger("Nuitka-Tools")
wheel_logger = OurLogger("Nuitka-Wheel", base_style="blue")
cache_logger = OurLogger("Nuitka-Cache")
reports_logger = OurLogger("Nuitka-Reports")
offsets_logger = OurLogger("Nuitka-Offsets")


def queryUser(question, choices, default, default_non_interactive):
    assert default in choices, (default, choices)
    assert default_non_interactive in choices, (default, choices)

    prompt = "%s? %s : " % (
        question,
        "/".join(
            "[%s]" % choice.title() if choice == default else choice.title()
            for choice in choices
        ),
    )

    # Integrates with progress bar by closing it.
    printLine(prompt, end="")
    flushStandardOutputs()

    try:
        reply = raw_input() or default
    except EOFError:
        reply = default_non_interactive

    if reply == "y":
        reply = "yes"

    return reply.lower()


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
