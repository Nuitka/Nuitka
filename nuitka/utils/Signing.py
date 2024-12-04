#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Signing of executables.

"""

from nuitka.Options import (
    getMacOSSignedAppName,
    getMacOSSigningIdentity,
    shallUseSigningForNotarization,
)
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
Access to the specified codesign certificate was not allowed. Please \
'allow all items' or when compiling with GUI available, enable prompting \
for the certificate in KeyChain Access application for this certificate."""
        )

    return None, stderr


def detectMacIdentity():
    output = executeToolChecked(
        logger=postprocessing_logger,
        command=["security", "find-identity"],
        absence_message="The 'security' program is used to scan for signing identities",
    )

    if str is not bytes:
        output = output.decode("utf8")

    signing_name = None
    result = None

    for line in output.splitlines():
        line = line.strip()

        if line.startswith("2)"):
            postprocessing_logger.sysexit(
                "More than one signing identity, auto mode cannot be used."
            )

        if line.startswith("1)"):
            parts = line.split(" ", 2)

            result = parts[1]
            signing_name = parts[2]

    if result is None:
        postprocessing_logger.sysexit(
            "Failed to detect any signing identity, auto mode cannot be used."
        )
    else:
        postprocessing_logger.info(
            "Using signing identity %s automatically." % signing_name
        )

    return result


def addMacOSCodeSignature(filenames):
    """Add the code signature to filenames.

    Args:
        filenames - The filenames to be signed.

    Returns:
        None

    Notes:
        This is macOS specific.
    """

    # Weak signing.
    identity = getMacOSSigningIdentity()

    if identity == "auto":
        identity = detectMacIdentity()

    command = [
        # Need to avoid Anaconda codesign.
        "/usr/bin/codesign",
        "-s",
        identity,
        "--force",
        "--deep",
        "--preserve-metadata=entitlements",
    ]

    macos_signed_app_name = getMacOSSignedAppName()

    if macos_signed_app_name is not None:
        command += [
            "-i",
            macos_signed_app_name,
        ]

    if shallUseSigningForNotarization():
        command.append("--options=runtime")

    assert type(filenames) is not str
    command.extend(filenames)

    with withMadeWritableFileMode(filenames):
        executeToolChecked(
            logger=postprocessing_logger,
            command=command,
            absence_message=_macos_codesign_usage,
            stderr_filter=_filterCodesignErrorOutput,
        )


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
