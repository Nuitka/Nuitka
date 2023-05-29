#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Time taking.

Mostly for measurements of Nuitka of itself, e.g. how long did it take to
call an external tool.
"""

from timeit import default_timer as timer

from nuitka.Tracing import general


class StopWatch(object):
    __slots__ = ("start_time", "end_time")

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = timer()

    def restart(self):
        self.start()

    def end(self):
        self.end_time = timer()

    stop = end

    def getDelta(self):
        if self.end_time is not None:
            return self.end_time - self.start_time
        else:
            return timer() - self.start_time


class TimerReport(object):
    """Timer that reports how long things took.

    Mostly intended as a wrapper for external process calls.
    """

    __slots__ = ("message", "decider", "logger", "timer", "min_report_time")

    def __init__(self, message, logger=None, decider=True, min_report_time=None):
        self.message = message

        # Shortcuts.
        if decider is True:
            decider = lambda: True
        elif decider is False:
            decider = lambda: False

        if logger is None:
            logger = general

        self.logger = logger
        self.decider = decider
        self.min_report_time = min_report_time

        self.timer = None

    def getTimer(self):
        return self.timer

    def __enter__(self):
        self.timer = StopWatch()
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
            self.logger.info(self.message % self.timer.getDelta())
