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

macos_codesign_usage = (
    "The 'codesign' is used to make signatures on macOS and required to be found."
)


def _filterSigntoolErrorOutput(stderr):
    stderr = b"\n".join(
        line
        for line in stderr.splitlines()
        if line
        if b"replacing existing signature" not in line
    )

    return stderr


def addMacOSCodeSignature(filenames, identity=None, entitlements_filename=None):
    """Remove the code signature from a filename.

    Args:
        filenames - The files to be signed.
        identity - Use this identity to sign, default adhoc signature.
        entitlements_filename - Apply these entitlements in signature.

    Returns:
        None

    Notes:
        This is macOS specific.
    """

    # Weak signing.
    if not identity:
        identity = "-"

    command = [
        "codesign",
        "-s",
        identity,
        "--force",
    ]

    # hardened runtime unless no good identity
    if identity != "-":
        command.append("--options=runtime")

    if entitlements_filename:
        command.append("--entitlements")
        command.append(entitlements_filename)

    assert type(filenames) is not str
    command.extend(filenames)

    with withMadeWritableFileMode(filenames):
        executeToolChecked(
            logger=postprocessing_logger,
            command=command,
            absence_message=macos_codesign_usage,
            stderr_filter=_filterSigntoolErrorOutput,
        )
