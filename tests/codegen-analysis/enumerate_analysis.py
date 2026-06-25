#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


from __future__ import print_function


def consume(values):
    total = 0

    for index, value in enumerate(values):
        total += index + value

    return total


def consume_with_start(values):
    total = 0

    for index, value in enumerate(values, 5):
        total += index + value

    return total


def consume_next(values):
    iterator = enumerate(values)

    return next(iterator)


def main():
    values = list(range(100))

    print(consume(values))
    print(consume_with_start(values))
    print(consume_next("abc"))


main()

#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
