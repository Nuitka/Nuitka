#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.Options import getMacOSSigningIdentity
from nuitka.Tracing import postprocessing_logger

from .Execution import executeToolChecked
from .FileOperations import withMadeWritableFileMode

_macos_codesign_usage = (
    "The 'codesign' is used to make signatures on macOS and required to be found."
)


def _filterCodesignErrorOutput(stderr):
    stderr = b"\n".join(
        line
        for line in stderr.splitlines()
        if line
        if b"replacing existing signature" not in line
    )

    if b"errSecInternalComponent" in stderr:
        postprocessing_logger.sysexit(
            """\
Access to the certificate is now allowed. Please allow all items or with
GUI, enable prompting for the certificate in KeyChain Access."""
        )

    return None, stderr


def addMacOSCodeSignature(filenames):
    """Remove the code signature from a filename.

    Args:
        filenames - The files to be signed.

    Returns:
        None

    Notes:
        This is macOS specific.
    """

    # Weak signing.
    identity = getMacOSSigningIdentity()

    command = [
        "codesign",
        "-s",
        identity,
        "--force",
        "--deep",
        "--preserve-metadata=entitlements",
        # TODO: This appears to be useful, but apparently doesn't work for all flavors of Python.
        # "--options=runtime",
    ]

    assert type(filenames) is not str
    command.extend(filenames)

    with withMadeWritableFileMode(filenames):
        executeToolChecked(
            logger=postprocessing_logger,
            command=command,
            absence_message=_macos_codesign_usage,
            stderr_filter=_filterCodesignErrorOutput,
        )
