#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#

import sys

class X:
    def __del__(self):
        print "X.__del__ occurred"

def raising(doit):
    _x = X()

    if doit:
        1 / 0

# Call it without an exception
raising(False)

def catcher():
    try:
        raising(True)
    except ZeroDivisionError:
        print "Catching"

        print "Top traceback code is '%s'." % sys.exc_info()[2].tb_frame.f_code.co_name
        print "Previous frame locals (module) are", sys.exc_info()[2].tb_next.tb_frame.f_locals
        pass

catcher()

print "Good bye."
