#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Internal tool, compression standalone distribution files and attach to onefile bootstrap binary.

"""

import os
import shutil
import struct
import sys
from contextlib import contextmanager

from nuitka.__past__ import to_byte
from nuitka.Progress import (
    closeProgressBar,
    enableProgressBar,
    reportProgressBar,
    setupProgressBar,
)
from nuitka.Tracing import onefile_logger
from nuitka.utils.AppDirs import getCacheDir
from nuitka.utils.FileOperations import (
    areSamePaths,
    getFileList,
    getFileSize,
    makePath,
)
from nuitka.utils.Hashing import Hash, HashCRC32
from nuitka.utils.Utils import (
    decoratorRetries,
    isWin32OrPosixWindows,
    isWin32Windows,
)
from nuitka.Version import version_string


def getCompressorLevel(low_memory):
    return 3 if low_memory else 22


def getCompressorFunction(expect_compression, low_memory):
    # spell-checker: ignore zstd, closefd

    if expect_compression:
        from zstandard import ZstdCompressor  # pylint: disable=I0021,import-error

        compressor_context = ZstdCompressor(level=getCompressorLevel(low_memory))

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


def _attachOnefilePayloadFile(
    output_file,
    is_archive,
    is_compressing,
    use_compression_cache,
    low_memory,
    file_compressor,
    filename_full,
    count,
    dist_dir,
    filename_encoding,
    file_checksums,
    win_path_sep,
):
    # Somewhat detail rich, at least unless we make more things mandatory, and
    # we also need to pass all modes, since this can be run in a separate process
    # that has no access to options.
    # pylint: disable=too-many-arguments,too-many-branches,too-many-locals,too-many-statements

    payload_item_size = 0

    filename_relative = os.path.relpath(filename_full, dist_dir)

    reportProgressBar(
        item=filename_relative,
        update=False,
    )

    # Might be changing from POSIX to Win32 Python on Windows.
    if win_path_sep:
        filename_relative = filename_relative.replace("/", "\\")
    else:
        filename_relative = filename_relative.replace("\\", "/")

    filename_encoded = (filename_relative + "\0").encode(filename_encoding)

    output_file.write(filename_encoded)
    payload_item_size += len(filename_encoded)

    file_flags = 0
    if not isWin32OrPosixWindows() and os.path.islink(filename_full):
        link_target = os.readlink(filename_full)

        file_flags |= 2
        file_header = to_byte(file_flags)

        output_file.write(file_header)
        payload_item_size += len(file_header)

        link_target_encoded = (link_target + "\0").encode(filename_encoding)

        output_file.write(link_target_encoded)
        payload_item_size += len(link_target_encoded)
    else:
        # This flag is only relevant for non-links.
        if not isWin32OrPosixWindows() and os.access(filename_full, os.X_OK):
            file_flags |= 1

        with open(filename_full, "rb") as input_file:
            input_file.seek(0, 2)
            input_size = input_file.tell()
            input_file.seek(0, 0)

            file_header = b""

            if not isWin32OrPosixWindows():
                file_header += to_byte(file_flags)

            file_header += struct.pack("Q", input_size)

            if file_checksums:
                hash_crc32 = HashCRC32()
                hash_crc32.updateFromFileHandle(input_file)
                input_file.seek(0, 0)

                # CRC32 value 0 is avoided, used as error indicator in C code.
                file_header += struct.pack("I", hash_crc32.asDigest() or 1)

            if is_archive and is_compressing:
                compression_cache_filename = _getCacheFilename(
                    binary_filename=filename_full, low_memory=low_memory
                )

                if not os.path.exists(compression_cache_filename):
                    with open(compression_cache_filename, "wb") as archive_entry_file:
                        with file_compressor(
                            archive_entry_file
                        ) as compressed_file_tmp2:
                            shutil.copyfileobj(input_file, compressed_file_tmp2)

                        compressed_size = archive_entry_file.tell()
                else:
                    compressed_size = getFileSize(compression_cache_filename)

                file_header += struct.pack("I", compressed_size)

            output_file.write(file_header)
            payload_item_size += len(file_header)

            if is_archive and is_compressing:
                with open(compression_cache_filename, "rb") as archive_entry_file:
                    pos1 = output_file.tell()
                    shutil.copyfileobj(archive_entry_file, output_file)
                    pos2 = output_file.tell()
                    assert pos2 - pos1 == compressed_size

                if count == 0 or not use_compression_cache:
                    os.unlink(compression_cache_filename)

                payload_item_size += compressed_size

            else:
                shutil.copyfileobj(input_file, output_file)
                payload_item_size += input_size

    reportProgressBar(
        item=filename_relative,
        update=True,
    )

    return payload_item_size


def _getCacheFilename(binary_filename, low_memory):
    hash_value = Hash()

    hash_value.updateFromFile(filename=binary_filename)

    # Have different values for different Python major versions.
    hash_value.updateFromValues(sys.version, sys.executable)

    # Take Nuitka version into account as well, ought to catch code changes.
    hash_value.updateFromValues(version_string)

    # Take zstandard version and compression level into account.
    from zstandard import __version__  # pylint: disable=I0021,import-error

    hash_value.updateFromValues(__version__, getCompressorLevel(low_memory))

    cache_dir = getCacheDir("onefile-compression")
    makePath(cache_dir)

    return os.path.join(cache_dir, hash_value.asHexDigest())


def _getInputFileList(dist_dir, start_binary):
    file_list = getFileList(dist_dir, normalize=False)
    file_list_size = len(file_list)
    file_list = [
        filename for filename in file_list if not areSamePaths(filename, start_binary)
    ]
    file_list.insert(0, start_binary)

    # If this fails, above code failed to find the start binary.
    assert file_list_size == len(file_list)

    return tuple(file_list)


def attachOnefilePayload(
    dist_dir,
    onefile_output_filename,
    start_binary,
    expect_compression,
    as_archive,
    use_compression_cache,
    file_checksums,
    win_path_sep,
    low_memory,
):
    compression_indicator, compressor = getCompressorFunction(
        expect_compression=expect_compression,
        low_memory=low_memory,
    )

    @decoratorRetries(
        logger=onefile_logger,
        purpose="write payload to '%s'" % onefile_output_filename,
        consequence="the result is unusable",
    )
    def _attachOnefilePayload():
        with open(onefile_output_filename, "ab") as output_file:
            # Seeking to end of file seems necessary on Python2 at least, maybe it's
            # just that tell reports wrong value initially.
            output_file.seek(0, 2)
            start_pos = output_file.tell()
            output_file.write(b"KA" + compression_indicator)

            # Move the binary to start immediately to the start position
            file_list = _getInputFileList(dist_dir=dist_dir, start_binary=start_binary)

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

            # Abstract the differences here for the time being.
            if as_archive:
                # Fake compressor then
                @contextmanager
                def overall_compressor(f):
                    yield f

                file_compressor = compressor
                is_archive = True
            else:
                overall_compressor = compressor

                @contextmanager
                def file_compressor(f):
                    yield f

                is_archive = False

            with overall_compressor(output_file) as compressed_file:
                for count, filename_full in enumerate(file_list, start=1):
                    payload_size += _attachOnefilePayloadFile(
                        output_file=compressed_file,
                        is_archive=is_archive,
                        file_compressor=file_compressor,
                        is_compressing=compression_indicator == b"Y",
                        use_compression_cache=use_compression_cache,
                        low_memory=low_memory,
                        filename_full=filename_full,
                        count=count,
                        dist_dir=dist_dir,
                        filename_encoding=filename_encoding,
                        file_checksums=file_checksums,
                        win_path_sep=win_path_sep,
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

            # TODO: If put into a resource, this is not really needed anymore.
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

    _attachOnefilePayload()


def main():
    # Internal tool, most simple command line handling. This is the build directory
    # where main Nuitka put the .const files.
    dist_dir = sys.argv[1]
    onefile_output_filename = sys.argv[2]
    start_binary = os.path.normpath(sys.argv[3])  # Might switch from MSYS2 to CPython
    file_checksums = sys.argv[4] == "True"
    win_path_sep = sys.argv[5] == "True"
    low_memory = sys.argv[6] == "True"
    as_archive = sys.argv[7] == "True"
    use_compression_cache = sys.argv[8] == "True"

    if os.getenv("NUITKA_PROGRESS_BAR") == "1":
        enableProgressBar()

    attachOnefilePayload(
        dist_dir=dist_dir,
        onefile_output_filename=onefile_output_filename,
        start_binary=start_binary,
        # We wouldn't be here, if that was not the case.
        expect_compression=True,
        as_archive=as_archive,
        use_compression_cache=use_compression_cache,
        file_checksums=file_checksums,
        win_path_sep=win_path_sep,
        low_memory=low_memory,
    )

    sys.exit(0)


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
