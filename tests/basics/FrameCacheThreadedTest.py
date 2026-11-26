#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Stress the frame cache from many threads."""

from __future__ import print_function

import sys
import threading

ITERATIONS = 500
THREAD_COUNT = 8


def cached(value):
    if value % 5 == 0:
        raise ValueError(value)

    return value + 1


def recursive(value):
    if value == 0:
        return 0

    return recursive(value - 1) + 1


def hold_frame(value):
    frame = sys._getframe()
    return frame.f_code.co_name


def worker(results, index, start_event):
    start_event.wait()

    total = 0
    errors = 0

    for i in range(ITERATIONS):
        try:
            total += cached(i + index)
        except ValueError:
            errors += 1

        total += recursive(5)
        hold_frame(i)

    results[index] = (total, errors)


def expected_result(index):
    total = 0
    errors = 0

    for i in range(ITERATIONS):
        try:
            total += cached(i + index)
        except ValueError:
            errors += 1

        total += recursive(5)

    return (total, errors)


def main():
    start_event = threading.Event()
    results = [None] * THREAD_COUNT
    threads = [
        threading.Thread(target=worker, args=(results, i, start_event))
        for i in range(THREAD_COUNT)
    ]

    for thread in threads:
        thread.start()

    start_event.set()

    for thread in threads:
        thread.join()

    for i in range(THREAD_COUNT):
        assert results[i] == expected_result(i), (i, results[i], expected_result(i))

    print("OK")


main()

#     Python tests originally created or extracted from other peoples work. The
#     parts were too small to be protected.
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
