#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Time taking.

Mostly for measurements of Nuitka of itself, e.g. how long did it take to
call an external tool.
"""

from contextlib import contextmanager

from nuitka.__past__ import StringIO, perf_counter, process_time
from nuitka.Tracing import general

from .Profiling import PerfCounters, hasPerfProfilingSupport

has_perf_counters = hasPerfProfilingSupport()


class StopWatchWallClockBase(object):
    __slots__ = ("start_time", "end_time", "perf_counters")

    # For overload, pylint: disable=not-callable
    timer = None

    def __init__(self, use_perf_counters=False):
        self.start_time = None
        self.end_time = None

        self.perf_counters = PerfCounters() if use_perf_counters else None

    def start(self):
        if self.perf_counters is not None:
            self.perf_counters.start()
        self.start_time = self.timer()

    def restart(self):
        self.start()

    def end(self):
        self.end_time = self.timer()

        if self.perf_counters is not None:
            self.perf_counters.stop()

    stop = end

    def getDelta(self):
        if self.end_time is not None:
            return self.end_time - self.start_time
        else:
            return self.timer() - self.start_time

    def getPerfCounters(self):
        if self.perf_counters is not None:
            return self.perf_counters.getValues()
        else:
            return None, None


class StopWatchWallClock(StopWatchWallClockBase):
    timer = perf_counter


class StopWatchProcessClock(StopWatchWallClockBase):
    timer = process_time


class TimerReport(object):
    """Timer that reports how long things took.

    Mostly intended as a wrapper for external process calls.
    """

    __slots__ = (
        "message",
        "decider",
        "logger",
        "timer",
        "min_report_time",
        "include_sleep_time",
        "use_perf_counters",
    )

    def __init__(
        self,
        message,
        logger=None,
        decider=True,
        min_report_time=None,
        include_sleep_time=True,
        use_perf_counters=None,
    ):
        self.message = message

        # Shortcuts.
        if decider is True:
            decider = lambda: 1
        elif decider is False:
            decider = lambda: 0

        if logger is None:
            logger = general

        self.logger = logger
        self.decider = decider
        self.min_report_time = min_report_time

        self.timer = None
        self.include_sleep_time = include_sleep_time

        if use_perf_counters is None:
            use_perf_counters = not self.include_sleep_time

        # They might not be allowed.
        self.use_perf_counters = use_perf_counters and has_perf_counters

    def getTimer(self):
        return self.timer

    def __enter__(self):
        stop_stop_class = (
            StopWatchWallClock if self.include_sleep_time else StopWatchProcessClock
        )
        self.timer = stop_stop_class(self.use_perf_counters)

        self.timer.start()

        return self.timer

    def __exit__(self, exception_type, exception_value, exception_tb):
        self.timer.end()

        delta_time = self.timer.getDelta()

        # Check if its above the provided limit.
        above_threshold = (
            self.min_report_time is None or delta_time >= self.min_report_time
        )

        if exception_type is None and above_threshold and self.decider():
            self.logger.info(self.message % self.timer.getDelta(), keep_format=True)


@contextmanager
def withProfiling(name, logger, enabled):
    if enabled:
        import cProfile
        import pstats

        from nuitka.options.Options import getOutputPath

        pr = cProfile.Profile(timer=process_time)
        pr.enable()

        yield

        pr.disable()

        s = StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats(pstats.SortKey.CUMULATIVE)

        ps.print_stats()
        for line in s.getvalue().splitlines():
            logger.info(line)

        profile_filename = getOutputPath(name + ".prof")

        pr.dump_stats(profile_filename)
        logger.info("Profiling data for '%s' saved to '%s'." % (name, profile_filename))
    else:
        yield


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
