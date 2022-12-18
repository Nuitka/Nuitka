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
""" Internal tool, compression standalone distribution files and attach to onefile bootstrap binary.

"""

import os
import shutil
import struct
import sys
import time
from contextlib import contextmanager

from nuitka.__past__ import to_byte
from nuitka.Progress import (
    closeProgressBar,
    enableProgressBar,
    reportProgressBar,
    setupProgressBar,
)
from nuitka.Tracing import onefile_logger
from nuitka.utils.FileOperations import getFileList
from nuitka.utils.Hashing import HashCRC32
from nuitka.utils.Utils import (
    isPosixWindows,
    isWin32OrPosixWindows,
    isWin32Windows,
)


def getCompressorFunction(expect_compression):
    # spell-checker: ignore zstd, closefd

    if expect_compression:
        from zstandard import ZstdCompressor  # pylint: disable=I0021,import-error

        compressor_context = ZstdCompressor(level=22)

        @contextmanager
        def useCompressedFile(output_file):
            with compressor_context.stream_writer(
                output_file, closefd=False
            ) as compressed_file:
                yield compressed_file

        onefile_logger.info("Using compression for onefile payload.")

        return b"Y", useCompressedFile
    else:

        @contextmanager
        def useSameFile(output_file):
            yield output_file

        return b"X", useSameFile


@contextmanager
def _openBinaryFileForAppending(onefile_output_filename):
    max_attempts = 5

    # TODO: This is code duplication with resource handling, should be unified
    # and with as a context manager.

    for attempt in range(1, max_attempts + 1):
        try:
            with open(onefile_output_filename, "ab") as output_file:
                if attempt != 1:
                    onefile_logger.warning(
                        "Succeeded to open binary for payload attachment in attempt %d."
                        % attempt
                    )

                yield output_file

                return
        except OSError as e:
            # Only for Windows at this time, other platforms don't have the issue.
            if not isWin32Windows() and not isPosixWindows():
                raise

            if e.errno in (110, 13):
                onefile_logger.warning(
                    """\
Failed to open binary for payload attachment in attempt %d.
Disable Anti-Virus, e.g. Windows Defender for build folders. Retrying after a second of delay."""
                    % attempt
                )
            else:
                onefile_logger.warning(
                    """\
Failed to open binary for payload attachment in attempt %d with error code %d.
Disable Anti-Virus, e.g. Windows Defender for build folders. Retrying after a second of delay."""
                    % (attempt, e.errno)
                )

            time.sleep(1)
            continue


def attachOnefilePayload(
    dist_dir, onefile_output_filename, start_binary, expect_compression, file_checksums
):
    # Somewhat detail rich, pylint: disable=too-many-locals,too-many-statements
    compression_indicator, compressor = getCompressorFunction(
        expect_compression=expect_compression
    )

    with _openBinaryFileForAppending(onefile_output_filename) as output_file:
        # Seeking to end of file seems necessary on Python2 at least, maybe it's
        # just that tell reports wrong value initially.
        output_file.seek(0, 2)
        start_pos = output_file.tell()
        output_file.write(b"KA" + compression_indicator)

        # Move the binary to start immediately to the start position
        file_list = getFileList(dist_dir, normalize=False)
        file_list.remove(start_binary)
        file_list.insert(0, start_binary)

        if isWin32Windows():
            filename_encoding = "utf-16le"
        else:
            filename_encoding = "utf8"

        payload_size = 0

        setupProgressBar(
            stage="Onefile Payload",
            unit="module",
            total=len(file_list),
        )

        with compressor(output_file) as compressed_file:
            for filename_full in file_list:
                filename_relative = os.path.relpath(filename_full, dist_dir)

                reportProgressBar(
                    item=filename_relative,
                    update=False,
                )

                filename_encoded = (filename_relative + "\0").encode(filename_encoding)

                compressed_file.write(filename_encoded)
                payload_size += len(filename_encoded)

                file_flags = 0
                if not isWin32OrPosixWindows() and os.access(filename_full, os.X_OK):
                    file_flags += 1

                with open(filename_full, "rb") as input_file:
                    input_file.seek(0, 2)
                    input_size = input_file.tell()
                    input_file.seek(0, 0)

                    file_header = struct.pack("Q", input_size)

                    if not isWin32OrPosixWindows():
                        file_header += to_byte(file_flags)

                    if file_checksums:
                        hash_crc32 = HashCRC32()
                        hash_crc32.updateFromFileHandle(input_file)
                        input_file.seek(0, 0)

                        # CRC32 value 0 is avoided, used as error indicator in C code.
                        file_header += struct.pack("I", hash_crc32.asDigest() or 1)

                    compressed_file.write(file_header)

                    shutil.copyfileobj(input_file, compressed_file)

                    payload_size += input_size + len(file_header)

                reportProgressBar(
                    item=filename_relative,
                    update=True,
                )

            # Using empty filename as a terminator.
            filename_encoded = "\0".encode(filename_encoding)
            compressed_file.write(filename_encoded)
            payload_size += len(filename_encoded)

            compressed_size = compressed_file.tell()

        if compression_indicator == b"Y":
            onefile_logger.info(
                "Onefile payload compression ratio (%.2f%%) size %d to %d."
                % (
                    (float(compressed_size) / payload_size) * 100,
                    payload_size,
                    compressed_size,
                )
            )

        if isWin32Windows():
            # add padding to have the start position at a double world boundary
            # this is needed on windows so that a possible certificate immediately
            # follows the start position
            pad = output_file.tell() % 8
            if pad != 0:
                output_file.write(bytes(8 - pad))

        output_file.seek(0, 2)
        end_pos = output_file.tell()

        # Size of the payload data plus the size of that size storage, so C code can
        # jump directly to it.
        output_file.write(struct.pack("Q", end_pos - start_pos))

    closeProgressBar()


def main():
    # Internal tool, most simple command line handling. This is the build directory
    # where main Nuitka put the .const files.
    dist_dir = sys.argv[1]
    onefile_output_filename = sys.argv[2]
    start_binary = os.path.normpath(sys.argv[3])  # Might switch from MSYS2 to CPython
    file_checksums = sys.argv[4] == "True"

    if os.environ.get("NUITKA_PROGRESS_BAR") == "1":
        enableProgressBar()

    attachOnefilePayload(
        dist_dir=dist_dir,
        onefile_output_filename=onefile_output_filename,
        start_binary=start_binary,
        # We wouldn't be here, if that was not the case.
        expect_compression=True,
        file_checksums=file_checksums,
    )

    sys.exit(0)
