#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


import sys

print("Testing exception changes between generator switches:")


def yieldExceptionInteraction():
    def yield_raise():
        try:
            raise KeyError("caught")
        except KeyError:
            yield from sys.exc_info()
            yield from sys.exc_info()
        yield from sys.exc_info()

    g = yield_raise()
    print("Initial yield from catch in generator", next(g))
    print("Checking from outside of generator", sys.exc_info()[0])
    print("Second yield from the catch reentered", next(g))
    print("Checking from outside of generator", sys.exc_info()[0])
    print("After leaving the catch generator yielded", next(g))


yieldExceptionInteraction()

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
