#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Windows COFF Object generation for payload embedding.

This module provides a pure-Python generator for PE/COFF .obj files
containing a single binary payload representing an "rdata" section.
It is used to bypass MSVC's lack of #embed.
"""

import shutil
import struct

from nuitka.utils.FileOperations import getFileSize


def generateWindowsCoffObject(in_filename, out_filename, symbol_name, architecture):
    """Generate a valid MSVC COFF .obj file containing the given payload.

    Args:
        in_filename (str): Path to the input binary payload.
        out_filename (str): Path to write the resulting .obj file.
        symbol_name (str): The C symbol name to export.
        architecture (str): 'x86', 'x64', or 'arm64'
    """

    # pylint: disable=too-many-locals
    arch_map = {
        "x86": 0x014C,  # IMAGE_FILE_MACHINE_I386
        "x86_64": 0x8664,  # IMAGE_FILE_MACHINE_AMD64
        "arm64": 0xAA64,  # IMAGE_FILE_MACHINE_ARM64
    }

    machine = arch_map.get(architecture.lower())
    if not machine:
        raise ValueError(
            "Unsupported architecture for COFF object generation: %s" % architecture
        )

    # For 32-bit x86, MSVC conventions require a leading underscore on C symbols.
    if architecture.lower() == "x86" and not symbol_name.startswith("_"):
        symbol_name = "_" + symbol_name

    if type(symbol_name) is bytes:
        symbol_bytes = symbol_name
    else:
        symbol_bytes = symbol_name.encode("utf8")

    if len(symbol_bytes) <= 8:
        sym_name_field = symbol_bytes.ljust(8, b"\x00")
        string_table = b""
    else:
        # String table format: 4-byte total size (including size field),
        # followed by null-terminated strings.
        string_table_data = symbol_bytes + b"\x00"
        string_table_size = 4 + len(string_table_data)
        string_table = struct.pack("<I", string_table_size) + string_table_data

        # In the 8-byte Name field for long symbols:
        # 0 (4 bytes), offset in string table (4 bytes)
        # The offset is 4 because the first string starts right after the 4-byte size field.
        sym_name_field = struct.pack("<II", 0, 4)

    payload_size = getFileSize(in_filename)

    # 4-byte alignment padding for the symbol table
    padding_len = (4 - (payload_size % 4)) % 4
    padding = b"\x00" * padding_len

    # Header sizes
    file_header_size = 20
    section_header_size = 40

    pointer_to_raw_data = file_header_size + section_header_size
    pointer_to_symbol_table = pointer_to_raw_data + payload_size + padding_len

    # 1. PE File Header
    file_header = struct.pack(
        "<HHIIIHH",  # spell-checker: ignore HHIIIHH
        machine,
        1,  # NumberOfSections
        0,  # TimeDateStamp (0 for reproducibility)
        pointer_to_symbol_table,
        1,  # NumberOfSymbols
        0,  # SizeOfOptionalHeader
        0,  # Characteristics
    )

    # 2. Section Header (.rdata), spell-checker: ignore rdata
    section_name = b".rdata\x00\x00"

    # Characteristics flags:
    # IMAGE_SCN_CNT_INITIALIZED_DATA = 0x00000040
    # IMAGE_SCN_ALIGN_16BYTES        = 0x00500000
    # IMAGE_SCN_MEM_READ             = 0x40000000
    section_characteristics = 0x40500040

    section_header = struct.pack(
        "<8sIIIIIIHHI",  # spell-checker: ignore IIIIIIHHI
        section_name,
        0,  # VirtualSize (0 for obj)
        0,  # VirtualAddress (0 for obj)
        payload_size,
        pointer_to_raw_data,
        0,  # PointerToRelocations
        0,  # PointerToLinenumbers
        0,  # NumberOfRelocations
        0,  # NumberOfLinenumbers
        section_characteristics,
    )

    # 3. Symbol Table Entry
    # Value is 0 (offset within section)
    # SectionNumber is 1 (1-based index to our section)
    # Type is 0 (IMAGE_SYM_TYPE_NULL)
    # StorageClass is 2 (IMAGE_SYM_CLASS_EXTERNAL)
    # NumberOfAuxSymbols is 0
    symbol_table_entry = struct.pack(
        "<8sIhHBB",
        sym_name_field,
        0,  # Value
        1,  # SectionNumber
        0,  # Type
        2,  # StorageClass
        0,  # NumberOfAuxSymbols
    )

    with open(out_filename, "wb") as f_out:
        f_out.write(file_header)
        f_out.write(section_header)

        with open(in_filename, "rb") as f_in:
            shutil.copyfileobj(f_in, f_out)

        f_out.write(padding)
        f_out.write(symbol_table_entry)
        f_out.write(string_table)


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
