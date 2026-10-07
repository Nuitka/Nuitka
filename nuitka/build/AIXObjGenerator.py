#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""AIX XCOFF Object generation for payload embedding.

This module provides a pure-Python generator for 64 bits XCOFF object
files containing a single binary payload representing a data csect.
It is used to bypass the need for large C source files with byte arrays.
"""

import shutil
import struct

from nuitka.utils.FileOperations import getFileSize

# XCOFF file header magic, only the 64 bits format is supported.
_XCOFF64_MAGIC = 0x01F7

# Section flags, only the initialized data is used here.
_STYP_DATA = 0x0040

# CSECT symbol types, the low 3 bits of 'x_smtyp'.
_XTY_SD = 1

# The alignment is the log2 of it, shifted left by 3 into 'x_smtyp'.
_SMTYP_ALIGNMENT_8 = 3 << 3

# Auxiliary entry type for CSECT entries in XCOFF64.
_AUX_CSECT = 251

# Storage mapping classes, read-only and read-write data.
_XMC_RO = 1
_XMC_RW = 5

# Symbol storage classes, C external symbol.
_C_EXT = 2

_FILE_HEADER_SIZE = 24
_SECTION_HEADER_SIZE = 72


def generateAIXXcoffObject(in_filename, out_filename, symbol_name, writeable):
    """Generate a valid AIX XCOFF64 .o file containing the given payload.

    Notes:
        This is intended to be used on AIX and PASE only, and always creates
        64 bits object files, the 32 bits format is not supported.

    Args:
        in_filename: Path to the input binary payload.
        out_filename: Path to write the resulting .o file.
        symbol_name: The C symbol name to export.
        writeable: Use a writable data csect (XMC_RW) instead of a
            read-only constant (XMC_RO).
    """
    symbol_bytes = symbol_name
    if str is not bytes:
        symbol_bytes = symbol_name.encode("utf8")

    payload_size = getFileSize(in_filename)

    # Align the payload end to 8 bytes for the symbol table behind it.
    payload_padding_len = (8 - (payload_size % 8)) % 8

    # 1. XCOFF64 file header.
    file_header = struct.pack(
        ">HHIQHHI",  # spell-checker: ignore HHIQHHI
        _XCOFF64_MAGIC,  # f_magic
        1,  # f_nscns
        0,  # f_timdat (0 for reproducibility)
        # f_symptr, points past the headers, payload and its padding.
        _FILE_HEADER_SIZE + _SECTION_HEADER_SIZE + payload_size + payload_padding_len,
        0,  # f_opthdr
        0,  # f_flags
        2,  # f_nsyms (one symbol with one auxiliary entry)
    )

    # 2. XCOFF64 section header for the '.data' section, uses the CSECT
    # storage mapping class to decide over read-only vs. writable.
    section_header = struct.pack(
        ">8sQQQQQQIIII",  # spell-checker: ignore QQQQQQIIII
        b".data\x00\x00\x00",
        0,  # s_paddr
        0,  # s_vaddr
        payload_size,  # s_size
        _FILE_HEADER_SIZE + _SECTION_HEADER_SIZE,  # s_scnptr, after headers
        0,  # s_relptr
        0,  # s_lnnoptr
        0,  # s_nreloc
        0,  # s_nlnno
        _STYP_DATA,  # s_flags
        0,  # s_pad
    )

    # 3. XCOFF64 symbol table entry, the name is in the string table.
    symbol_table_entry = struct.pack(
        ">QIhHBB",
        0,  # n_value
        4,  # n_offset_ (offset of the name in the string table)
        1,  # n_scnum
        0,  # n_type
        _C_EXT,  # n_sclass
        1,  # n_numaux
    )

    # 4. XCOFF64 CSECT auxiliary entry defining the data section, the
    # section length is split into low and high 32 bits.
    aux_entry = struct.pack(
        ">IIHBBIBB",
        payload_size & 0xFFFFFFFF,  # x_scnlen_lo
        0,  # x_parmhash
        0,  # x_snhash
        (_XTY_SD | _SMTYP_ALIGNMENT_8),  # x_smtyp (csect def, 8 bytes aligned)
        _XMC_RW if writeable else _XMC_RO,  # x_smclas
        payload_size >> 32,  # x_scnlen_hi
        0,  # x_pad
        _AUX_CSECT,  # x_auxtype
    )

    # 5. String table with the symbol name, the size includes its own field.
    string_table = struct.pack(">I", 4 + len(symbol_bytes) + 1)
    string_table += symbol_bytes + b"\x00"

    with open(out_filename, "wb") as f_out:
        f_out.write(file_header)
        f_out.write(section_header)

        with open(in_filename, "rb") as f_in:
            shutil.copyfileobj(f_in, f_out)

        f_out.write(b"\x00" * payload_padding_len)
        f_out.write(symbol_table_entry)
        f_out.write(aux_entry)
        f_out.write(string_table)


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
