#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Progress bar for Scons compilation part.

This does only the interfacing with tracing and collection of information.

"""

from nuitka.Progress import (
    closeProgressBar,
    enableProgressBar,
    reportProgressBar,
    setupProgressBar,
)
from nuitka.Tracing import scons_logger


def enableSconsProgressBar():
    enableProgressBar()

    import atexit

    atexit.register(closeSconsProgressBar)


_total = None
_current = 0
_stage = None


def setSconsProgressBarTotal(name, total):
    # keep track of how many files there are to know when link comes, pylint: disable=global-statement
    global _total, _stage
    _total = total
    _stage = name

    setupProgressBar(stage="%s C" % name, unit="file", total=total)


def updateSconsProgressBar():
    # Check if link is next, pylint: disable=global-statement
    global _current
    _current += 1

    reportProgressBar(item=None, update=True)

    if _current == _total:
        closeSconsProgressBar()

        message = "%s C linking" % _stage

        if _total > 1:
            message += (
                " with %d files (no progress information available for this stage)"
                % _total
            )

        message += "."

        scons_logger.info(message)


def closeSconsProgressBar():
    closeProgressBar()


def reportSlowCompilation(env, cmd, delta_time):
    # TODO: for linking, we ought to apply a different timer maybe and attempt to extra
    # the source file that is causing the issues: pylint: disable=unused-argument
    if _current != _total:
        scons_logger.info(
            """\
Slow C compilation detected, used %.0fs so far, scalability problem."""
            % delta_time
        )
    else:
        if env.orig_lto_mode == "auto" and env.lto_mode:
            scons_logger.info(
                """\
Slow C linking detected, used %.0fs so far, consider using '--lto=no' \
for faster linking, or '--lto=yes"' to disable this message. """
                % delta_time
            )


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
