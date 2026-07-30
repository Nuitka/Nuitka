#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Progress bar for Scons compilation part.

This does only the interfacing with tracing and collection of information.

"""

import time

from nuitka.Progress import (
    closeProgressBar,
    enableProgressBar,
    reportProgressBar,
    setupProgressBar,
)
from nuitka.Tracing import scons_logger


def enableSconsProgressBar(progress_bar):
    enableProgressBar(progress_bar)

    import atexit

    atexit.register(closeSconsProgressBar)


_total = None
_current = 0
_stage = None

# Backend phase timing (wall clock + summed process deltas).
_phase_wall_start = None
_compile_finished_wall = None
_link_finished_wall = None
_compile_process_time = 0.0
_link_process_time = 0.0
_compile_jobs = 0
_link_jobs = 0
_phase_report_emitted = False


def setSconsProgressBarTotal(name, total):
    # keep track of how many files there are to know when link comes, pylint: disable=global-statement
    global _total, _stage, _phase_wall_start, _compile_finished_wall
    global _link_finished_wall, _compile_process_time, _link_process_time
    global _compile_jobs, _link_jobs, _phase_report_emitted, _current

    _total = total
    _stage = name
    _current = 0
    _phase_wall_start = time.time()
    _compile_finished_wall = None
    _link_finished_wall = None
    _compile_process_time = 0.0
    _link_process_time = 0.0
    _compile_jobs = 0
    _link_jobs = 0
    _phase_report_emitted = False

    setupProgressBar(stage="%s C" % name, unit="file", total=total)

    # Scons runs targets after the .scons script body; emit phase stats on exit.
    import atexit

    atexit.register(noteSconsBackendFinished)


def recordSconsSpawnTiming(is_link, process_delta):
    """Record one compiler/linker spawn duration for phase breakdown."""
    # pylint: disable=global-statement
    global _compile_process_time, _link_process_time, _compile_jobs, _link_jobs

    if process_delta is None:
        process_delta = 0.0

    if is_link:
        _link_process_time += process_delta
        _link_jobs += 1
    else:
        _compile_process_time += process_delta
        _compile_jobs += 1


def getSconsBackendPhaseStats():
    """Return compile/link phase timing collected for the current scons run."""
    compile_wall = None
    link_wall = None
    total_wall = None

    if _phase_wall_start is not None:
        end_wall = _link_finished_wall or _compile_finished_wall or time.time()
        total_wall = end_wall - _phase_wall_start

        if _compile_finished_wall is not None:
            compile_wall = _compile_finished_wall - _phase_wall_start
            if _link_finished_wall is not None:
                link_wall = _link_finished_wall - _compile_finished_wall
        elif _link_finished_wall is not None:
            # Link-only style runs (or no compile updates).
            link_wall = _link_finished_wall - _phase_wall_start

    return {
        "compile_jobs": _compile_jobs,
        "link_jobs": _link_jobs,
        "compile_process_time": _compile_process_time,
        "link_process_time": _link_process_time,
        "compile_wall": compile_wall,
        "link_wall": link_wall,
        "total_wall": total_wall,
    }


def reportSconsBackendPhaseTiming():
    """Log compile vs link timing once at the end of the backend."""
    # pylint: disable=global-statement
    global _phase_report_emitted

    if _phase_report_emitted:
        return

    stats = getSconsBackendPhaseStats()
    if stats["total_wall"] is None:
        return

    _phase_report_emitted = True

    compile_wall = stats["compile_wall"]
    link_wall = stats["link_wall"]

    scons_logger.info(
        "Backend phase timing: compile wall %.2fs (process-sum %.2fs, %d job(s)), "
        "link wall %.2fs (process-sum %.2fs, %d job(s)), total wall %.2fs."
        % (
            compile_wall if compile_wall is not None else 0.0,
            stats["compile_process_time"],
            stats["compile_jobs"],
            link_wall if link_wall is not None else 0.0,
            stats["link_process_time"],
            stats["link_jobs"],
            stats["total_wall"],
        )
    )


def updateSconsProgressBar():
    # Check if link is next, pylint: disable=global-statement
    global _current, _compile_finished_wall
    _current += 1

    reportProgressBar(item=None, update=True)

    if _current == _total:
        closeSconsProgressBar()
        _compile_finished_wall = time.time()

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


def noteSconsBackendFinished():
    """Mark backend finished and emit phase timing."""
    # pylint: disable=global-statement
    global _link_finished_wall, _compile_finished_wall

    if _link_finished_wall is None:
        _link_finished_wall = time.time()

    # If we never reached compile completion (e.g. total==0), still close.
    if _compile_finished_wall is None and _phase_wall_start is not None:
        _compile_finished_wall = _phase_wall_start

    reportSconsBackendPhaseTiming()


def reportSlowCompilation(env, cmd, delta_time):
    # TODO: for linking, we ought to apply a different timer maybe and attempt to extra
    # the source file that is causing the issues: pylint: disable=unused-argument
    if _current != _total:
        scons_logger.info("""\
Slow C compilation detected, used %.0fs so far, scalability problem.""" % delta_time)
    else:
        if env.orig_lto_mode == "auto" and env.lto_mode:
            scons_logger.info("""\
Slow C linking detected, used %.0fs so far, consider using '--lto=no' \
for faster linking, or '--lto=yes"' to disable this message. """ % delta_time)


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
