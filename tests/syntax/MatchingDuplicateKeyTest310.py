#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# Test that duplicate constant keys in a mapping pattern are rejected at
# compile time, like CPython does. The ast module doesn't check this, so the
# compiler has to do it explicitly.

match {"a": 1}:
    case {"a": x, "a": y}:
        pass

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
