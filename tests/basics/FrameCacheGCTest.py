#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Test that idle compiled frame caches are invisible to the garbage collector."""

from __future__ import print_function

import gc
import sys


class Marker(object):
    pass


held_frames = []
markers = []


def compiled_frame_names():
    result = []

    for obj in gc.get_objects():
        if type(obj).__name__ == "compiled_frame":
            result.append(obj.f_code.co_name)

    return result


def count_compiled_frames(name):
    return compiled_frame_names().count(name)


def assert_tracked(frame):
    if hasattr(gc, "is_tracked"):
        assert gc.is_tracked(frame)


def check_current_frame_visible():
    frame = sys._getframe()

    if type(frame).__name__ == "compiled_frame":
        assert_tracked(frame)
        assert any(obj is frame for obj in gc.get_objects())


def simple(value):
    return value + 1


def hold_frame(append):
    if append:
        held_frames.append(sys._getframe())

    return None


def store_marker():
    marker = Marker()
    markers.append(marker)
    sys._getframe().f_locals["marker"] = marker

    return None


def exception_frame(local_value):
    raise ValueError(local_value)


def recursive(value):
    if value:
        return recursive(value - 1)

    return 0


def simple_generator():
    yield 1
    yield 2


def capture_returned_frame():
    return sys._getframe()


def main():
    gc.collect()
    assert count_compiled_frames("simple") == 0

    for i in range(100):
        simple(i)

    gc.collect()
    assert count_compiled_frames("simple") == 0

    hold_frame(True)
    assert len(held_frames) == 1

    if type(held_frames[0]).__name__ == "compiled_frame":
        assert_tracked(held_frames[0])

    del held_frames[:]
    gc.collect()

    # The cached frame can stay tracked until it is claimed again. The next
    # call must clean it up and return it to the idle state.
    hold_frame(False)
    gc.collect()
    assert count_compiled_frames("hold_frame") == 0

    store_marker()
    del markers[:]
    gc.collect()
    assert not any(isinstance(obj, Marker) for obj in gc.get_objects())

    try:
        exception_frame("traceback-locals")
    except ValueError:
        exception_tb = sys.exc_info()[2]
        exception_frame_obj = None

        while exception_tb is not None:
            if exception_tb.tb_frame.f_code.co_name == "exception_frame":
                exception_frame_obj = exception_tb.tb_frame
                break

            exception_tb = exception_tb.tb_next

        assert exception_frame_obj is not None
        assert exception_frame_obj.f_locals.get("local_value") == "traceback-locals"

        if type(exception_frame_obj).__name__ == "compiled_frame":
            assert_tracked(exception_frame_obj)

        del exception_tb
        del exception_frame_obj

    # Python 2 keeps the last exception state on the executing frame, which can
    # keep the traceback frame alive until it is cleared.
    if hasattr(sys, "exc_clear"):
        sys.exc_clear()

    gc.collect()
    assert count_compiled_frames("exception_frame") == 0

    generator = simple_generator()
    next(generator)

    if type(generator.gi_frame).__name__ == "compiled_frame":
        assert_tracked(generator.gi_frame)

    list(generator)
    del generator
    gc.collect()
    assert count_compiled_frames("simple_generator") == 0

    recursive(10)
    gc.collect()
    assert count_compiled_frames("recursive") == 0

    frame = sys._getframe()
    assert frame.f_back is not None

    if type(frame.f_back).__name__ == "compiled_frame":
        assert_tracked(frame.f_back)

    check_current_frame_visible()

    if hasattr(frame, "clear"):
        captured = capture_returned_frame()
        captured.clear()

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
