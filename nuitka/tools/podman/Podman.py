#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Podman container usage tools. """

from nuitka.utils.Execution import getExecutablePath
from nuitka.utils.Utils import (
    isDebianBasedLinux,
    isFedoraBasedLinux,
    isLinux,
    isWin32Windows,
)


def getPodmanExecutablePath(logger):
    result = getExecutablePath("podman")

    if getExecutablePath("podman") is None:
        if isWin32Windows():
            logger.sysexit(
                """\
Cannot find 'podman'. Install it from \
'https://github.com/containers/podman/blob/main/docs/tutorials/podman-for-windows.md'."""
            )
        elif isLinux():
            if isDebianBasedLinux():
                logger.sysexit(
                    "Cannot find 'podman'. Install it with 'apt-get install podman'."
                )
            elif isFedoraBasedLinux():
                logger.sysexit(
                    "Cannot find 'podman'. Install it with 'dnf install podman'."
                )
            else:
                logger.sysexit(
                    "Cannot find 'podman'. Install it with your package manager."
                )

    return result
