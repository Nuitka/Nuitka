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
from __future__ import print_function

print("Module name is", __name__)

class SomeClass:
    pass

print("Class inside main module names its module as", repr(SomeClass.__module__))

if __name__ == "__main__":
    print("Executed as __main__:")

    import sys, os

    # The sys.argv[0] might contain ".exe", ".py" or no suffix at all.
    # Remove it, so the "diff" output is more acceptable.
    args = sys.argv[:]
    args[0] = os.path.basename(args[0]).replace(".exe", ".py").replace(".py", "")

    print("Arguments were (stripped argv[0] suffix):", repr(args))

    # Output the flags, so we can test if we are compatible with these too.
    print("The sys.flags are:", sys.flags)
