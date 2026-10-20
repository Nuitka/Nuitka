#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Test Python 3.14 template strings with conversions."""

width = 10


def dump(template):
    print("strings:", template.strings)
    for interpolation in template.interpolations:
        print(
            "interpolation:",
            repr(interpolation.value),
            repr(interpolation.expression),
            repr(interpolation.conversion),
            repr(interpolation.format_spec),
        )


dump(t"hi {'world'!r}")
dump(t"{'world'!s}")
dump(t"{'world'!a}")
dump(t"{1 + 2!r}")
dump(t"{'x'!s:>10}")
dump(t"{'x'!a:{width}}")
dump(t"before {'value'!r} after")

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
