#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Stress Nuitka's static free lists from many threads."""

from __future__ import print_function

import sys
import threading

ITERATIONS = 300
THREAD_COUNT = 8


class C(object):
    def method(self, value):
        return value + 1


def cached(value):
    return value + 1


def make_function(value):
    def nested():
        return value

    return nested


def make_generator(value):
    yield value
    yield value + 1


def make_traceback(value):
    try:
        raise ValueError(value)
    except ValueError:
        return sys.exc_info()[2]


def worker(results, index, start_event):
    start_event.wait()

    total = 0

    for i in range(ITERATIONS):
        function = make_function(i)
        total += function()

        instance = C()
        total += instance.method(i)

        generator = make_generator(i)
        total += next(generator)
        generator.close()

        traceback = make_traceback(i)
        total += traceback.tb_lineno
        del traceback

        total += cached(i)

    results[index] = total


def expected_result():
    total = 0

    for i in range(ITERATIONS):
        function = make_function(i)
        total += function()

        instance = C()
        total += instance.method(i)

        generator = make_generator(i)
        total += next(generator)
        generator.close()

        traceback = make_traceback(i)
        total += traceback.tb_lineno
        del traceback

        total += cached(i)

    return total


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

    expected = expected_result()

    for i in range(THREAD_COUNT):
        assert results[i] == expected, (i, results[i], expected)

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
