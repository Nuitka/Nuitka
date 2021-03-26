#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
import os

print(
    "This is",
    __name__,
    "code with error raise",
    os.environ.get("TEST_SHALL_RAISE_ERROR"),
)


class Class3(object):
    pass


def raiseError():
    raise Exception("AHOJ")


if os.environ.get("TEST_SHALL_RAISE_ERROR") == "1":
    raiseError()


class Class5(object):
    pass
