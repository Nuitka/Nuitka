#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Internal tool, compression standalone distribution files and attach to onefile bootstrap binary."""

import os
import shutil
import struct
import sys
from collections import namedtuple
from contextlib import contextmanager

from nuitka.Progress import (
    enableProgressBar,
    reportProgressBar,
    withProgressBar,
)
from nuitka.PythonVersions import is32BitPython
from nuitka.Tracing import onefile_logger
from nuitka.utils.FileOperations import areSamePaths, getFileList, getFileSize
from nuitka.utils.Hashing import HashCRC32
from nuitka.utils.Json import loadJsonFromFilename
from nuitka.utils.Utils import (
    decoratorRetries,
    isWin32OrPosixWindows,
    isWin32Windows,
)

# The payload starts with a table of contents, so that unpacked files can be
# validated without decompressing the payload, and without a separate cache
# manifest file.
_PAYLOAD_MAGIC = b"KAYKAY!"

_PAYLOAD_ENTRY_FLAG_EXECUTABLE = 1
_PAYLOAD_ENTRY_FLAG_SYMLINK = 2
_PAYLOAD_ENTRY_FLAG_LAST = 4

# The magic is only present in debug builds, it is a development aid only.
# The "=" prefix keeps native endianness with standard sizes and no padding.
_PAYLOAD_HEADER_STRUCT_DEBUG = struct.Struct("=7sQQ")
_PAYLOAD_HEADER_STRUCT_RELEASE = struct.Struct("=QQ")

# Temporary mode has no checksums, so the CRC field is omitted there.
_PAYLOAD_ENTRY_STRUCT_CHECKSUMS = struct.Struct("=IIQ")
_PAYLOAD_ENTRY_STRUCT_NO_CHECKSUMS = struct.Struct("=IQ")

_PayloadEntry = namedtuple(
    "_PayloadEntry",
    (
        "encoded_name",
        "encoded_link_target",
        "flags",
        "crc32",
        "size",
        "source_filename",
    ),
)

_PayloadDesc = namedtuple(
    "_PayloadDesc",
    (
        "onefile_output_filename",
        "dist_dir",
        "file_checksums",
        "win_path_sep",
        "compressor",
        "is_compressing",
        "debug_mode",
    ),
)


def getCompressorLevel(low_memory):
    return 3 if low_memory else 22


def getCompressorFunction(expect_compression, low_memory, job_limit):
    # spell-checker: ignore closefd

    # On 32-bit Python, zstandard stream_writer at level 22 with threads >= 1
    # fails with "Allocation error : not enough memory" even for tiny data,
    # so we must use single-threaded compression on 32-bit.
    effective_threads = 0 if low_memory or is32BitPython() else job_limit

    if expect_compression:
        try:
            from compression import zstd

            # Some libzstd builds lack multithreading support, in which case the
            # valid range for 'nb_workers' is (0, 0), and passing a larger value
            # is an error.
            nb_workers_min, nb_workers_max = (
                zstd.CompressionParameter.nb_workers.bounds()
            )
            effective_threads = min(
                max(effective_threads, nb_workers_min), nb_workers_max
            )

            @contextmanager
            def useCompressedFile(output_file):
                with zstd.open(
                    output_file,
                    mode="wb",
                    options={
                        zstd.CompressionParameter.nb_workers: effective_threads,
                        zstd.CompressionParameter.compression_level: getCompressorLevel(
                            low_memory
                        ),
                    },
                ) as compressed_file:
                    yield compressed_file

        except ImportError:
            from zstandard import (  # pylint: disable=I0021,import-error
                ZstdCompressor,
                ZstdError,
            )

            compression_level = getCompressorLevel(low_memory)

            try:
                compressor_context = ZstdCompressor(
                    level=compression_level, threads=effective_threads
                )
            except ZstdError:
                if not effective_threads:
                    raise

                # Some libzstd builds lack multithreading support, and reject
                # any positive 'threads' value.
                compressor_context = ZstdCompressor(level=compression_level, threads=0)

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


def _getPayloadEntry(
    filename_full,
    dist_dir,
    filename_encoding,
    file_checksums,
    win_path_sep,
):
    filename_relative = os.path.relpath(filename_full, dist_dir)

    # Might be changing from POSIX to Win32 Python on Windows.
    if win_path_sep:
        filename_relative = filename_relative.replace("/", "\\")
    else:
        filename_relative = filename_relative.replace("\\", "/")

    filename_encoded = (filename_relative + "\0").encode(filename_encoding)

    if not isWin32OrPosixWindows() and os.path.islink(filename_full):
        link_target_encoded = (os.readlink(filename_full) + "\0").encode(
            filename_encoding
        )

        return _PayloadEntry(
            encoded_name=filename_encoded,
            encoded_link_target=link_target_encoded,
            flags=_PAYLOAD_ENTRY_FLAG_SYMLINK,
            crc32=None,
            size=0,
            source_filename=None,
        )

    file_flags = 0

    # This flag is only relevant for non-links.
    if not isWin32OrPosixWindows() and os.access(filename_full, os.X_OK):
        file_flags |= _PAYLOAD_ENTRY_FLAG_EXECUTABLE

    input_size = getFileSize(filename_full)

    if file_checksums:
        # The on-wire format uses 0 to indicate no checksum, so a real CRC32
        # of 0 is stored as 1 instead.
        crc32 = HashCRC32().updateFromFile(filename=filename_full).asDigest() or 1
    else:
        crc32 = None

    return _PayloadEntry(
        encoded_name=filename_encoded,
        encoded_link_target=None,
        flags=file_flags,
        crc32=crc32,
        size=input_size,
        source_filename=filename_full,
    )


def _getPayloadToc(entries, file_checksums):
    toc_chunks = []

    for entry_index, entry in enumerate(entries):
        flags = entry.flags

        if entry_index == len(entries) - 1:
            flags |= _PAYLOAD_ENTRY_FLAG_LAST

        if file_checksums:
            toc_chunks.append(
                _PAYLOAD_ENTRY_STRUCT_CHECKSUMS.pack(
                    flags,
                    entry.crc32 if entry.crc32 is not None else 0,
                    entry.size,
                )
            )
        else:
            toc_chunks.append(
                _PAYLOAD_ENTRY_STRUCT_NO_CHECKSUMS.pack(flags, entry.size)
            )

        toc_chunks.append(entry.encoded_name)

        if entry.encoded_link_target is not None:
            toc_chunks.append(entry.encoded_link_target)

    return b"".join(toc_chunks)


def _getPayloadEntries(file_list, payload_desc):
    if isWin32Windows():
        filename_encoding = "utf-16le"
    else:
        filename_encoding = "utf8"

    entries = []

    with withProgressBar(
        stage="Onefile Packing",
        unit="module",
        total=len(file_list),
    ):
        for filename_full in file_list:
            entries.append(
                _getPayloadEntry(
                    filename_full=filename_full,
                    dist_dir=payload_desc.dist_dir,
                    filename_encoding=filename_encoding,
                    file_checksums=payload_desc.file_checksums,
                    win_path_sep=payload_desc.win_path_sep,
                )
            )

            reportProgressBar(
                item=os.path.relpath(filename_full, payload_desc.dist_dir),
                update=True,
            )

    return tuple(entries)


def _writePayloadToc(output_file, entries, debug_mode, file_checksums):
    toc_data = _getPayloadToc(entries=entries, file_checksums=file_checksums)

    if debug_mode:
        output_file.write(
            _PAYLOAD_HEADER_STRUCT_DEBUG.pack(
                _PAYLOAD_MAGIC,
                len(toc_data),
                0,  # body size, patched later once known
            )
        )
        body_size_offset = 15
    else:
        output_file.write(
            _PAYLOAD_HEADER_STRUCT_RELEASE.pack(
                len(toc_data),
                0,  # body size, patched later once known
            )
        )
        body_size_offset = 8

    output_file.write(toc_data)

    return body_size_offset


def _writePayloadBody(output_file, file_list, entries, payload_desc):
    @contextmanager
    def useBodyFile(body_file):
        yield body_file

    with withProgressBar(
        stage="Onefile Contents",
        unit="module",
        total=len(file_list),
    ):
        if payload_desc.is_compressing:
            body_context = payload_desc.compressor(output_file)
        else:
            body_context = useBodyFile(output_file)

        with body_context as body_file:
            for filename_full, entry in zip(file_list, entries):
                if entry.source_filename is not None:
                    with open(entry.source_filename, "rb") as input_file:
                        shutil.copyfileobj(input_file, body_file)

                reportProgressBar(
                    item=os.path.relpath(filename_full, payload_desc.dist_dir),
                    update=True,
                )

        return output_file.tell()


def _writeOnefilePayload(file_list, payload_desc):
    entries = _getPayloadEntries(file_list, payload_desc)

    with open(payload_desc.onefile_output_filename, "ab") as output_file:
        # Seeking to end of file seems necessary on Python2 at least, maybe it's
        # just that tell reports wrong value initially.
        output_file.seek(0, 2)
        start_pos = output_file.tell()

        body_size_offset = _writePayloadToc(
            output_file=output_file,
            entries=entries,
            debug_mode=payload_desc.debug_mode,
            file_checksums=payload_desc.file_checksums,
        )

        body_start = output_file.tell()
        payload_size = sum(entry.size for entry in entries)

        body_end = _writePayloadBody(
            output_file=output_file,
            file_list=file_list,
            entries=entries,
            payload_desc=payload_desc,
        )

        # TODO: If put into a resource, this is not really needed anymore.
        if isWin32Windows():
            # add padding to have the start position at a double word boundary
            # this is needed on windows so that a possible certificate immediately
            # follows the start position
            pad = output_file.tell() % 8
            if pad != 0:
                output_file.write(bytes(8 - pad))

        output_file.seek(0, 2)
        end_pos = output_file.tell()

        if payload_desc.is_compressing and payload_size != 0:
            stored_size = end_pos - start_pos

            onefile_logger.info(
                "Onefile payload compression ratio (%.2f%%) size %d to %d."
                % (
                    (float(stored_size) / payload_size) * 100,
                    payload_size,
                    stored_size,
                )
            )

        # Size of the payload data plus the size of that size storage, so C code can
        # jump directly to it.
        output_file.write(struct.pack("=Q", end_pos - start_pos))

    # The body size is only known after compressing it, patch the header that
    # was already written.
    with open(payload_desc.onefile_output_filename, "rb+") as patch_file:
        patch_file.seek(start_pos + body_size_offset)
        patch_file.write(struct.pack("<Q", body_end - body_start))


def _getInputFileList(dist_dir, start_binary, include_start_binary, expected_files):
    file_list = getFileList(dist_dir, normalize=False)
    file_list_size = len(file_list)
    file_list = [
        filename for filename in file_list if not areSamePaths(filename, start_binary)
    ]

    if expected_files is not None:
        expected_files_set = set(
            os.path.normcase(os.path.normpath(f)) for f in expected_files
        )

        start_binary_relative_norm = os.path.normcase(
            os.path.normpath(os.path.relpath(start_binary, dist_dir))
        )
        if start_binary_relative_norm in expected_files_set:
            expected_files_set.remove(start_binary_relative_norm)

        for filename in file_list:
            filename_relative = os.path.relpath(filename, dist_dir)
            filename_relative_norm = os.path.normcase(
                os.path.normpath(filename_relative)
            )

            if filename_relative_norm not in expected_files_set:
                onefile_logger.warning(
                    """\
Distribution folder contains unexpected file '%s', this file will be ignored in future release."""
                    % filename_relative
                )
            else:
                expected_files_set.remove(filename_relative_norm)

        for missing_file in expected_files_set:
            onefile_logger.warning(
                """\
Distribution folder is missing expected file '%s'. This might cause issues."""
                % missing_file
            )

    if include_start_binary:
        file_list.insert(0, start_binary)

    # If this fails, above code failed to find the start binary.
    assert file_list_size == len(file_list) + (0 if include_start_binary else 1)

    return tuple(file_list)


def attachOnefilePayload(
    dist_dir,
    onefile_output_filename,
    start_binary,
    include_start_binary,
    expect_compression,
    file_checksums,
    debug_mode,
    win_path_sep,
    low_memory,
    job_limit,
    expected_files,
):
    compression_indicator, compressor = getCompressorFunction(
        expect_compression=expect_compression,
        low_memory=low_memory,
        job_limit=job_limit,
    )

    @decoratorRetries(
        logger=onefile_logger,
        purpose="write payload to '%s'" % onefile_output_filename,
        consequence="the result is unusable",
    )
    def _attachOnefilePayload():
        file_list = _getInputFileList(
            dist_dir=dist_dir,
            start_binary=start_binary,
            include_start_binary=include_start_binary,
            expected_files=expected_files,
        )

        _writeOnefilePayload(
            file_list=file_list,
            payload_desc=_PayloadDesc(
                onefile_output_filename=onefile_output_filename,
                dist_dir=dist_dir,
                file_checksums=file_checksums,
                win_path_sep=win_path_sep,
                compressor=compressor,
                is_compressing=compression_indicator == b"Y",
                debug_mode=debug_mode,
            ),
        )

    _attachOnefilePayload()


def main():
    # Internal tool, most simple command line handling. This is the build directory
    # where main Nuitka put the .const files.
    dist_dir = sys.argv[1]
    onefile_output_filename = sys.argv[2]
    start_binary = os.path.normpath(sys.argv[3])  # Might switch from MSYS2 to CPython
    include_start_binary = sys.argv[4] == "True"
    file_checksums = sys.argv[5] == "True"
    debug_mode = sys.argv[6] == "True"
    win_path_sep = sys.argv[7] == "True"
    low_memory = sys.argv[8] == "True"
    job_limit = int(sys.argv[9])
    expected_files_filename = sys.argv[10]

    expected_files = tuple(loadJsonFromFilename(expected_files_filename))

    enableProgressBar(os.getenv("NUITKA_PROGRESS_BAR", "none"))

    attachOnefilePayload(
        dist_dir=dist_dir,
        onefile_output_filename=onefile_output_filename,
        start_binary=start_binary,
        include_start_binary=include_start_binary,
        # We wouldn't be here, if that was not the case.
        expect_compression=True,
        file_checksums=file_checksums,
        debug_mode=debug_mode,
        win_path_sep=win_path_sep,
        low_memory=low_memory,
        job_limit=job_limit,
        expected_files=expected_files,
    )

    sys.exit(0)


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
