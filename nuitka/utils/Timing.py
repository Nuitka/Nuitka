#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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

from logging import info
from timeit import default_timer as timer

from nuitka.Options import isShowProgress


class StopWatch(object):
    __slots__ = ("start_time", "end_time")

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = timer()

    def end(self):
        self.end_time = timer()

    def delta(self):
        return self.end_time - self.start_time


class TimerReport(object):
    """ Timer that reports how long things took.

        Mostly intended as a wrapper for external process calls.
    """

    __slots__ = ("message", "timer")

    def __init__(self, message):
        self.message = message
        self.timer = None

    def __enter__(self):
        self.timer = StopWatch()
        self.timer.start()

    def __exit__(self, exception_type, exception_value, exception_tb):
        self.timer.end()

        if exception_type is None and isShowProgress():
            info(self.message % self.timer.delta())
