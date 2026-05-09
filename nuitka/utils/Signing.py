#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Signing of executables."""

import re

from nuitka.options.Options import (
    getMacOSSignedAppName,
    getMacOSSigningCertificateFilename,
    getMacOSSigningCertificatePassword,
    getMacOSSigningIdentity,
    shallUseSigningForNotarization,
)
from nuitka.Tracing import postprocessing_logger

from .Execution import executeToolChecked
from .FileOperations import getExternalUsePath, withMadeWritableFileMode

_macos_codesign_usage = (
    "The 'codesign' is used to make signatures on macOS and required to be found."
)

_macos_security_usage = (
    "The 'security' is used to access signatures from files on macOS."
)

_macos_find_identity_pattern = re.compile(
    r'^\s*\d+\)\s+([0-9A-F]+)\s+"(.*)"(?:\s+\(.*\))?$'
)


def _filterCodesignErrorOutput(stderr, signing_identity, signing_keychain_filename):
    stderr = b"\n".join(
        line
        for line in stderr.splitlines()
        if line
        if b"replacing existing signature" not in line
        if b"unable to build chain to self-signed root" not in line
    )

    if b"errSecInternalComponent" in stderr:
        details = []

        if signing_identity is not None:
            details.append("identity '%s'" % signing_identity)

        if signing_keychain_filename is not None:
            details.append("keychain '%s'" % signing_keychain_filename)

        if details:
            details = " Requested %s." % " and ".join(details)
        else:
            details = ""

        return postprocessing_logger.sysexit("""\
The macOS codesign step failed with a keychain access error \
'errSecInternalComponent'. This can mean that the signing identity is \
missing, incomplete, locked, or not accessible to codesign. Check that the \
requested identity exists with its private key and that the relevant keychain \
can be unlocked and used for code signing.%s""" % details)

    return None, stderr


def _filterSecurityErrorOutput(stderr):
    # TODO: Probably some errors are given if it already exists.
    return None, stderr


def _getMacOSCodeSigningIdentities(signing_keychain_filename):
    command = ["security", "find-identity", "-p", "codesigning"]

    if signing_keychain_filename is None:
        command.append("-v")

    if signing_keychain_filename is not None:
        command.append(signing_keychain_filename)

    output = executeToolChecked(
        logger=postprocessing_logger,
        command=command,
        absence_message="The 'security' program is used to scan for signing identities",
        stderr_filter=_filterSecurityErrorOutput,
        decoding=str is not bytes,
    )

    result = []
    seen_identities = set()

    for line in output.splitlines():
        match = _macos_find_identity_pattern.match(line)

        if match is None:
            continue

        identity_hash, signing_name = match.groups()

        if identity_hash in seen_identities:
            continue

        seen_identities.add(identity_hash)
        result.append((identity_hash, signing_name))

    return tuple(result)


def _unlockMacIdentityKeychain(signing_keychain_filename):
    command = [
        "security",
        "unlock-keychain",
        "-p",
        getMacOSSigningCertificatePassword() or "",
        signing_keychain_filename,
    ]

    executeToolChecked(
        logger=postprocessing_logger,
        command=command,
        absence_message=_macos_security_usage,
        stderr_filter=_filterSecurityErrorOutput,
    )


def _detectMacOSCodeSigningIdentity(signing_keychain_filename=None):
    identities = _getMacOSCodeSigningIdentities(
        signing_keychain_filename=signing_keychain_filename
    )

    if len(identities) > 1:
        found_names = ", ".join(
            "'%s'" % signing_name for _identity_hash, signing_name in identities
        )

        if signing_keychain_filename is None:
            return postprocessing_logger.sysexit(
                "More than one signing identity, auto mode cannot be used. Found: %s."
                % found_names
            )
        else:
            return postprocessing_logger.sysexit(
                "More than one code signing identity in keychain '%s', auto mode cannot be used. Found: %s."
                % (signing_keychain_filename, found_names)
            )

    if not identities:
        if signing_keychain_filename is None:
            return postprocessing_logger.sysexit(
                "Failed to detect any signing identity, auto mode cannot be used."
            )
        else:
            return postprocessing_logger.sysexit(
                "Failed to detect any code signing identity in keychain '%s', auto mode cannot be used."
                % signing_keychain_filename
            )

    identity_hash, signing_name = identities[0]

    if signing_keychain_filename is None:
        postprocessing_logger.info(
            "Using signing identity %s automatically." % signing_name
        )
    else:
        postprocessing_logger.info(
            "Using signing identity %s from keychain '%s' automatically."
            % (signing_name, signing_keychain_filename)
        )

    if signing_keychain_filename is not None:
        return signing_name
    else:
        return identity_hash


def addMacOSCodeSignature(filenames, entitlements_filename):
    """Add the code signature to filenames.

    Args:
        filenames - The filenames to be signed.
        entitlements_filename - The entitlements file to use, optional.

    Returns:
        None

    Notes:
        This is macOS specific.
    """

    # Weak signing.
    identity = getMacOSSigningIdentity()

    signing_keychain_filename = getMacOSSigningCertificateFilename()

    if signing_keychain_filename is not None:
        signing_keychain_filename = getExternalUsePath(signing_keychain_filename)
        _unlockMacIdentityKeychain(signing_keychain_filename)

    if identity == "auto":
        identity = _detectMacOSCodeSigningIdentity(
            signing_keychain_filename=signing_keychain_filename
        )

    command = [
        # Need to avoid Anaconda codesign.
        "/usr/bin/codesign",
        "-s",
        identity,
        "--force",
        "--deep",
        "--preserve-metadata=entitlements",
    ]

    if signing_keychain_filename is not None:
        command += [
            "--keychain",
            signing_keychain_filename,
        ]

    macos_signed_app_name = getMacOSSignedAppName()

    if macos_signed_app_name is not None:
        command += [
            "-i",
            macos_signed_app_name,
        ]

    if entitlements_filename is not None:
        command += [
            "--entitlements",
            getExternalUsePath(entitlements_filename),
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
            context={
                "signing_identity": identity,
                "signing_keychain_filename": signing_keychain_filename,
            },
        )


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
