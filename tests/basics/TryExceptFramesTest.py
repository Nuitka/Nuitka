#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


from __future__ import print_function

import sys


def displayDict(d):
    if "__loader__" in d:
        d = dict(d)
        d["__loader__"] = "<__loader__ removed>"

    if "__file__" in d:
        d = dict(d)
        d["__file__"] = "<__file__ removed>"

    import pprint

    return pprint.pformat(d)


counter = 1


class X:
    def __init__(self):
        global counter
        self.counter = counter
        counter += 1

    def __del__(self):
        print("X.__del__ occurred", self.counter)


def raising(doit):
    _x = X()

    def nested():
        if doit:
            1 / 0

    try:
        return nested()
    except ZeroDivisionError:
        print("Changing closure variable value.")
        # This is just to prove that closure variables get updates in frame
        # locals.
        doit = 5
        raise


# Call it without an exception
raising(False)


def catcher():
    try:
        raising(True)
    except ZeroDivisionError:
        print("Caught.")

        print("Top traceback code is '%s'." % sys.exc_info()[2].tb_frame.f_code.co_name)
        print(
            "Second traceback code is '%s'."
            % sys.exc_info()[2].tb_next.tb_frame.f_code.co_name
        )
        print(
            "Third traceback code is '%s'."
            % sys.exc_info()[2].tb_next.tb_next.tb_frame.f_code.co_name
        )
        print(
            "Third traceback locals (function) are",
            displayDict(sys.exc_info()[2].tb_next.tb_next.tb_frame.f_locals),
        )


catcher()

print("Good bye.")

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
