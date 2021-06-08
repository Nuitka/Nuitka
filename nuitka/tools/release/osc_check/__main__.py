#!/usr/bin/env python
#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
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

""" OpenSUSE Build Service (OSC) status check.

Confirms that all relevant packages are successfully built. For use in
Buildbot on a timer basis.

"""


from __future__ import print_function

import csv
import sys

from nuitka.__past__ import StringIO
from nuitka.utils.Execution import check_output


def main():
    print("Querying openSUSE build service status of Nuitka packages.")

    osc_cmd = ["osc", "pr", "-c", "home:kayhayen"]

    stdout_osc = check_output(args=osc_cmd)

    # Response is really a CSV file, so use that for parsing.
    csvfile = StringIO(stdout_osc)
    osc_reader = csv.reader(csvfile, delimiter=";")

    osc_reader = iter(osc_reader)

    bad = ("failed", "unresolvable", "broken", "blocked")

    titles = osc_reader.next()[1:]

    # Nuitka (follow git main branch)
    row1 = osc_reader.next()
    # Nuitka-Unstable (follow git develop branch)
    row2 = osc_reader.next()

    problems = []

    def decideConsideration(title):
        # Ignore other arch builds, they might to not even boot at times.
        if "ppc" in title or "aarch" in title or "arm" in title:
            return False

        # This fails for other reasons often, and is not critical to Nuitka.
        if "openSUSE_Tumbleweed" in title:
            return False

        return True

    for count, title in enumerate(titles):
        if not decideConsideration(title):
            continue

        status = row1[count + 1]

        if status in bad:
            problems.append((row1[0], title, status))

    for count, title in enumerate(titles):
        if not decideConsideration(title):
            continue

        status = row2[count + 1]

        if status in bad:
            problems.append((row2[0], title, status))

    if problems:
        print("There are problems with:")
        print("\n".join("%s: %s (%s)" % problem for problem in problems))

        sys.exit(1)
    else:
        print("Looks good.")
        sys.exit(0)


if __name__ == "__main__":
    main()
