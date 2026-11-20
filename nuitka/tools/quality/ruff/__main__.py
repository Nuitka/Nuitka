#!/usr/bin/env python
#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Main program for ruff checker tool."""

import sys

from nuitka.Tracing import tools_logger
from nuitka.utils.Execution import callProcess
from nuitka.utils.PrivatePipSpace import (
    getPrivatePipSitePackagesEnvironment,
    getRuffBinaryPath,
)


def main():
    args = sys.argv[1:]

    assume_yes_for_downloads = "--assume-yes-for-downloads" in args

    if assume_yes_for_downloads:
        args = [arg for arg in args if arg != "--assume-yes-for-downloads"]

    ruff_binary = getRuffBinaryPath(
        logger=tools_logger,
        assume_yes_for_downloads=assume_yes_for_downloads,
    )

    if ruff_binary is None:
        return tools_logger.sysexit("Error, cannot find 'ruff' binary.")

    if not args:
        args = ["nuitka/"]

    return callProcess(
        [ruff_binary, "check"] + args,
        env=getPrivatePipSitePackagesEnvironment(binary_path=ruff_binary),
    )


if __name__ == "__main__":
    sys.exit(main())

#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
