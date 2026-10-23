#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Signing of executables."""

import os
import re
from contextlib import contextmanager

from nuitka.options.Options import (
    getMacOSSignedAppName,
    getMacOSSigningCertificateFilename,
    getMacOSSigningCertificatePassword,
    getMacOSSigningIdentity,
    shallUseSigningForNotarization,
)
from nuitka.Tracing import postprocessing_logger

from .Execution import executeToolChecked
from .FileOperations import (
    copyFile,
    getExternalUsePath,
    withMadeWritableFileMode,
    withTemporaryFilename,
)

_macos_codesign_usage = (
    "The 'codesign' is used to make signatures on macOS and required to be found."
)

_macos_security_usage = (
    "The 'security' is used to access signatures from files on macOS."
)

_macos_find_identity_pattern = re.compile(
    r'^\s*\d+\)\s+([0-9A-F]+)\s+"(.*)"(?:\s+\(.*\))?$'
)

_macos_identity_hash_pattern = re.compile(r"^[0-9A-Fa-f]{40}$")


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
    password = getMacOSSigningCertificatePassword() or ""

    # Unlock the keychain. This alone works interactively, but in non-interactive
    # contexts (CI, SSH) the keychain will auto-lock again (fixed below) and
    # codesign will still hit ACL restrictions on the private key (also fixed
    # below).
    executeToolChecked(
        logger=postprocessing_logger,
        command=[
            "security",
            "unlock-keychain",
            "-p",
            password,
            signing_keychain_filename,
        ],
        absence_message=_macos_security_usage,
        stderr_filter=_filterSecurityErrorOutput,
    )

    # Prevent the keychain from re-locking during the codesign step. The
    # "-lut 21600" pattern is the standard macOS CI recipe: lock on sleep
    # (-l), enable timeout-based locking (-u), with a 6-hour window (-t
    # 21600). Without this, SSH/CI sessions will see the keychain lock
    # almost immediately after unlock.
    executeToolChecked(
        logger=postprocessing_logger,
        command=[
            "security",
            "set-keychain-settings",
            "-lut",
            "21600",
            signing_keychain_filename,
        ],
        absence_message=_macos_security_usage,
        stderr_filter=_filterSecurityErrorOutput,
    )

    # Allow Apple-signed tools (including /usr/bin/codesign) to access private
    # keys in the keychain without an interactive prompt. Without this, running
    # codesign in a non-interactive context (CI, SSH) will fail with
    # errSecInternalComponent because the security framework cannot show the
    # "codesign wants to sign using key..." dialog.
    executeToolChecked(
        logger=postprocessing_logger,
        command=[
            "security",
            "set-key-partition-list",
            "-S",
            "apple-tool:,apple:",
            "-s",
            "-k",
            password,
            signing_keychain_filename,
        ],
        absence_message=_macos_security_usage,
        stderr_filter=_filterSecurityErrorOutput,
    )


def _getMacOSKeychainSearchList():
    """Get the list of keychains 'codesign' searches for signing identities.

    Returns:
        list of str - Keychain filenames in the user's search list.
    """
    output = executeToolChecked(
        logger=postprocessing_logger,
        command=["security", "list-keychains", "-d", "user"],
        absence_message=_macos_security_usage,
        stderr_filter=_filterSecurityErrorOutput,
        decoding=str is not bytes,
    )

    result = []

    for line in output.splitlines():
        line = line.strip()

        if line.startswith('"') and line.endswith('"'):
            line = line[1:-1]

        if line:
            result.append(line)

    return result


def _setMacOSKeychainSearchList(keychain_filenames):
    """Set the list of keychains 'codesign' searches for signing identities.

    Args:
        keychain_filenames - list of str - Keychain filenames to use.

    Returns:
        None
    """
    executeToolChecked(
        logger=postprocessing_logger,
        command=["security", "list-keychains", "-d", "user", "-s"]
        + list(keychain_filenames),
        absence_message=_macos_security_usage,
        stderr_filter=_filterSecurityErrorOutput,
    )


@contextmanager
def _withMacOSKeychainInSearchList(signing_keychain_filename):
    """Make a keychain visible to 'codesign' for the duration of the context.

    'codesign' only searches the user's keychain search list for signing
    identities. The '--keychain' option alone does not make a keychain that is
    not in that list usable, so a temporary copy used for signing has to be
    added to the search list temporarily and the previous list restored
    afterwards.

    Args:
        signing_keychain_filename - Filename of the keychain to add.

    Yields:
        None
    """
    old_search_list = _getMacOSKeychainSearchList()

    _setMacOSKeychainSearchList(
        [signing_keychain_filename]
        + [
            keychain_filename
            for keychain_filename in old_search_list
            if keychain_filename != signing_keychain_filename
            if os.path.exists(keychain_filename)
        ]
    )

    try:
        yield
    finally:
        # Only remove our own entry, so that concurrent signings that added
        # theirs meanwhile keep working.
        _setMacOSKeychainSearchList(
            [
                keychain_filename
                for keychain_filename in _getMacOSKeychainSearchList()
                if keychain_filename != signing_keychain_filename
            ]
        )


@contextmanager
def withUnlockedMacIdentityKeychain(signing_keychain_filename):
    """Unlock a macOS keychain for codesign without dirtying the original.

    Args:
        signing_keychain_filename: Original keychain path or None.

    Yields:
        None if no keychain was given, otherwise the path of an unlocked
        temporary copy that is cleaned up on exit. The original file is
        never modified (``security`` commands change the file in place).

    Notes:
        ``security unlock-keychain`` / ``set-keychain-settings`` /
        ``set-key-partition-list`` modify the keychain file in place
        (timestamps / ACL). When the keychain is the checked-in
        this would dirty the git worktree, so we operate on a git-ignored
        temporary copy. Since ``codesign`` only searches the keychain search
        list, the temporary copy is added to it while signatures are made.
    """
    if signing_keychain_filename is None:
        yield None
        return

    signing_keychain_filename = getExternalUsePath(signing_keychain_filename)

    with withTemporaryFilename(
        prefix=".nuitka-keychain-",
        suffix=".tmp",
        temp_path=os.path.dirname(signing_keychain_filename) or ".",
    ) as tmp_filename:
        copyFile(signing_keychain_filename, tmp_filename)

        with _withMacOSKeychainInSearchList(tmp_filename):
            _unlockMacIdentityKeychain(tmp_filename)

            yield tmp_filename


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

    # Use the hash rather than the name, because other keychains in the
    # search list may contain an identity with the same name, which codesign
    # would consider ambiguous.
    return identity_hash


def _resolveMacOSCodeSigningIdentity(signing_identity, signing_keychain_filename):
    """Resolve a signing identity name to its hash in the given keychain.

    Args:
        signing_identity - The identity name requested by the user.
        signing_keychain_filename - The keychain to look the identity up in.

    Returns:
        str - Unique hash of the identity.

    Notes:
        This is macOS specific.
    """
    if _macos_identity_hash_pattern.match(signing_identity):
        return signing_identity

    identities = _getMacOSCodeSigningIdentities(
        signing_keychain_filename=signing_keychain_filename
    )

    matching_identities = tuple(
        (identity_hash, signing_name)
        for identity_hash, signing_name in identities
        if signing_name == signing_identity
    )

    if not matching_identities:
        return postprocessing_logger.sysexit(
            "Failed to detect code signing identity '%s' in keychain '%s'."
            % (signing_identity, signing_keychain_filename)
        )

    if len(matching_identities) > 1:
        return postprocessing_logger.sysexit(
            "More than one code signing identity named '%s' in keychain '%s', cannot be used."
            % (signing_identity, signing_keychain_filename)
        )

    identity_hash, _signing_name = matching_identities[0]

    # Use the hash rather than the name, because other keychains in the
    # search list may contain an identity with the same name, which codesign
    # would consider ambiguous.
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

    with withUnlockedMacIdentityKeychain(
        getMacOSSigningCertificateFilename()
    ) as signing_keychain_filename:
        if identity == "auto":
            signing_identity = _detectMacOSCodeSigningIdentity(
                signing_keychain_filename=signing_keychain_filename
            )
            signing_identity_display = signing_identity
        elif signing_keychain_filename is not None:
            signing_identity = _resolveMacOSCodeSigningIdentity(
                signing_identity=identity,
                signing_keychain_filename=signing_keychain_filename,
            )
            signing_identity_display = identity
        else:
            signing_identity = identity
            signing_identity_display = identity

        command = [
            # Need to avoid Anaconda codesign.
            "/usr/bin/codesign",
            "-s",
            signing_identity,
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
                    "signing_identity": signing_identity_display,
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
