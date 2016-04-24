#!/usr/bin/python
#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

import os
import sys
from optparse import OptionParser

parser = OptionParser()

parser.add_option(
    "--mode",
    action  = "store",
    dest    = "mode",
    default = "release",
    help    = """\
The mode of update, prerelease, hotfix, or final."""
)
options, positional_args = parser.parse_args()

if positional_args:
    parser.print_help()

    sys.exit("\nError, no positional argument allowed.")

# Go its own directory, to have it easy with path knowledge.
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

option_lines = [ line for line in open("nuitka/Options.py") ]

version_line, = [ line for line in open("nuitka/Options.py") if line.startswith("Nuitka V") ]

old_version = version_line[ 8:].rstrip()

if options.mode.startswith("pre"):
    if "rc" in old_version:
        parts = old_version.split("rc")

        new_version = "rc".join([parts[0], str(int(parts[1]) + 1) ])
    else:
        old_version = '.'.join(old_version.split('.')[:3])
        parts = old_version.split('.')
        parts[-1] = str(int(parts[-1]) + 1)

        new_version = '.'.join(parts) + "rc1"
elif options.mode == "release":
    if "rc" in old_version:
        old_version = old_version[ : old_version.find("rc") ]
        was_pre = True
    else:
        was_pre = False

    new_version = '.'.join(old_version.split('.')[:3])

    if not was_pre:
        parts = new_version.split('.')
        parts[-1] = str(int(parts[-1]) + 1)

        new_version = '.'.join(parts)
elif options.mode == "hotfix":
    assert "pre" not in old_version and "rc" not in old_version

    parts = old_version.split('.')

    if len(parts) == 3:
        parts.append('1')
    else:
        parts[-1] = str(int(parts[-1]) + 1)

    new_version = '.'.join(parts)

else:
    sys.exit("Error, unknown mode '%s'." % options.mode)

# Above code should succeed set this variable
assert new_version

with open("nuitka/Options.py", 'w') as options_file:
    for line in option_lines:
        if line.startswith("Nuitka V"):
            line = "Nuitka V" + new_version + '\n'

        options_file.write(line)

print old_version, "->", new_version
debian_version = new_version.replace("rc", "~rc") + "+ds-1"

if "rc" in new_version:
    if "rc1" in new_version:
        os.system('debchange -R "New upstream pre-release."')
        os.system('debchange --newversion=%s ""'  % debian_version)
    else:
        os.system('debchange --newversion=%s ""'  % debian_version)
else:
    if "rc" in version_line:
        # Initial final release after pre-releases.
        changelog_lines = open("debian/changelog").readlines()
        with open("debian/changelog", 'w') as output:
            first = True
            for line in changelog_lines[1:]:
                if line.startswith("nuitka") and first:
                    first = False

                if not first:
                    output.write(line)

        os.system('debchange -R "New upstream release."')
        os.system('debchange --newversion=%s ""'  % debian_version)
    else:
        # Hotfix release after previous final or hotfix release.
        os.system('debchange -R "New upstream hotfix release."')
        os.system('debchange --newversion=%s ""'  % debian_version)

    os.system('debchange -r ""')
