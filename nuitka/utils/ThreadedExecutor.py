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
""" Threaded pool execution.

This can use Python3 native, Python2.7 backport, or has a Python2.6 stub that
does not thread at all.
"""

from threading import Lock

try:
    from concurrent.futures import (
        ThreadPoolExecutor,
        wait,
        as_completed,
        FIRST_EXCEPTION,
    )  # @UnresolvedImport pylint: disable=I0021,import-error,no-name-in-module,unused-import

    def waitWorkers(workers):
        wait(workers, return_when=FIRST_EXCEPTION)

        for future in as_completed(workers):
            yield future.result()


except ImportError:
    # No backport installed, use stub for at least Python 2.6, and potentially
    # also Python 2.7, we might want to tell the user about it though, that
    # we think it should be installed.
    class ThreadPoolExecutor(object):
        def __init__(self, max_workers=None):
            # This stub ignores max_workers, pylint: disable=unused-argument

            self.results = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, exc_traceback):
            return False

        def submit(self, function, *args):
            # Submitted jobs are simply done immediately.
            self.results.append(function(*args))

            return self

    def waitWorkers(workers):
        if workers:
            return iter(workers[0].results)


assert Lock
assert ThreadPoolExecutor
