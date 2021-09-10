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
""" Signing of executables.

"""

from nuitka.Tracing import postprocessing_logger

from .Execution import executeToolChecked
from .FileOperations import withMadeWritableFileMode

_macos_codesign_usage = "The 'codesign' is used to remove invalidated signatures on macOS and required to be found."


def removeMacOSCodeSignature(filename):
    """Remove the code signature from a filename.

    Args:
        filename - The file to be modified.

    Returns:
        None

    Notes:
        This is macOS specific.
    """

    with withMadeWritableFileMode(filename):
        executeToolChecked(
            logger=postprocessing_logger,
            command=["codesign", "--remove-signature", "--all-architectures", filename],
            absence_message=_macos_codesign_usage,
        )


def addMacOSCodeSignature(filename, identity, entitlements_filename, deep):
    extra_args = []

    # Weak signing is supported.
    if not identity:
        identity = "-"

    command = [
        "codesign",
        "-s",
        identity,
        "--force",
        "--timestamp",
        "--all-architectures",
    ]

    # hardened runtime unless no good identify
    if identity != "-":
        extra_args.append("--options=runtime")

    if entitlements_filename:
        extra_args.append("--entitlements")
        extra_args.append(entitlements_filename)

    if deep:
        extra_args.append("--deep")

    command.append(filename)

    with withMadeWritableFileMode(filename):
        executeToolChecked(
            logger=postprocessing_logger,
            command=command,
            absence_message=_macos_codesign_usage,
        )
