#!/usr/bin/env python
#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" OpenSUSE Build Service (OSC) status check.

Confirms that all relevant packages are successfully built. For use in
Buildbot on a timer basis.

"""


import csv
import sys

from nuitka.__past__ import StringIO
from nuitka.tools.environments.Virtualenv import withVirtualenv
from nuitka.Tracing import my_print, tools_logger
from nuitka.utils.InstalledPythons import findInstalledPython


def main():
    # TODO: The setup of the osc virtualenv ought to be shared.
    # many cases, pylint: disable=too-many-branches,too-many-locals,too-many-statements

    my_print("Querying openSUSE build service status of Nuitka packages.")

    # spell-checker: ignore kayhayen
    osc_cmd = "osc pr -c home:kayhayen"

    installed_python = findInstalledPython(
        python_versions=("3.10",), module_name=None, module_version=None
    )

    with withVirtualenv(
        "venv_nuitka",
        logger=tools_logger,
        style="blue",
        python=installed_python.getPythonExe(),
    ) as venv:
        venv.runCommand("python -m pip install osc")

        stdout_osc, stderr, exit_code = venv.runCommandWithOutput(osc_cmd)

        assert exit_code == 0, stderr

    if str is not bytes:
        stdout_osc = stdout_osc.decode("utf8")

    # Response is really a CSV file, so use that for parsing.
    csv_file = StringIO(stdout_osc)
    osc_reader = csv.reader(csv_file, delimiter=";")

    osc_reader = iter(osc_reader)

    bad = ("failed", "unresolvable", "broken", "blocked")

    titles = next(osc_reader)[1:]

    # Nuitka (follow git main branch)
    row1 = next(osc_reader)
    # Nuitka-Unstable (follow git develop branch)
    row2 = next(osc_reader)
    # Nuitka-Experimental (follow git factory branch)
    row3 = next(osc_reader)

    problems = []

    def decideConsideration(title, status):
        # Ignore other arch builds, they might to not even boot at times.
        # spell-checker: ignore aarch
        if "ppc" in title or "aarch" in title or "arm" in title:
            return False

        # This fails for other reasons often, and is not critical to Nuitka.
        if "openSUSE_Tumbleweed" in title:
            return False

        # Ignore old Fedora and RHEL6 32 bit being blocked.
        if status == "blocked":
            if (
                "Fedora_2" in title
                or "RedHat_RHEL-6/i586" in title
                or "CentOS_CentOS-6/i586" in title
            ):
                return False

        # It makes building visible now, that's not an error of course.
        if status == "building":
            return False

        # It makes need to build visible as well, that too is not an error
        # really.
        if status == "outdated":
            return False

        return True

    for count, title in enumerate(titles):
        status = row1[count + 1]

        if not decideConsideration(title, status):
            continue

        if status in bad:
            problems.append((row1[0], title, status))

    for count, title in enumerate(titles):
        status = row2[count + 1]

        if not decideConsideration(title, status):
            continue

        if status in bad:
            problems.append((row2[0], title, status))

    for count, title in enumerate(titles):
        status = row3[count + 1]

        if not decideConsideration(title, status):
            continue

        if status in bad:
            problems.append((row3[0], title, status))

    if problems:
        my_print("There are problems with:", style="yellow")
        my_print(
            "\n".join("%s: %s (%s)" % problem for problem in problems), style="yellow"
        )

        if any(problem[0] == "Nuitka" for problem in problems):
            my_print(
                "Check here: https://build.opensuse.org/package/show/home:kayhayen/Nuitka"
            )

        if any(problem[0] == "Nuitka-Unstable" for problem in problems):
            my_print(
                "Check here: https://build.opensuse.org/package/show/home:kayhayen/Nuitka-Unstable"
            )

        if any(problem[0] == "Nuitka-experimental" for problem in problems):
            my_print(
                "Check here: https://build.opensuse.org/package/show/home:kayhayen/Nuitka-experimental"
            )

        sys.exit(1)
    else:
        my_print("Looks good.", style="blue")
        sys.exit(0)


if __name__ == "__main__":
    main()

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
