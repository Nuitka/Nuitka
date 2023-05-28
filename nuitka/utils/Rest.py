#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Work with ReST documentations.

This e.g. creates PDF documentations during release and tables from data
for the web site, e.g. downloads.

"""

import functools
import os
import tempfile

from .Execution import check_call, withEnvironmentVarOverridden
from .FileOperations import (
    changeFilenameExtension,
    deleteFile,
    getFileContents,
    putTextFileContents,
)


def createPDF(document):
    pdf_filename = changeFilenameExtension(document, ".pdf")
    args = ["-o", pdf_filename]

    with tempfile.NamedTemporaryFile(delete=False) as style_file:
        style_filename = style_file.name
        style_file.write(
            b"""
"pageSetup" : {
   "firstTemplate": "coverPage"
}

"styles" : [
       [ "title" , {
           "fontName": "NanumGothic-Bold",
           "fontSize": 40
       } ],
       [ "heading1" , {
           "fontName": "NanumGothic-Bold"
       } ],
       [ "heading2" , {
           "fontName": "NanumGothic"
       } ]
]
"""
        )

    if document != "Changelog.rst":
        args.append("-s")
        args.append(style_filename)

        args.append('--header="###Title### - ###Section###"')
        args.append('--footer="###Title### - page ###Page### - ###Section###"')

    # Workaround for rst2pdf not support ..code:: without language.
    old_contents = getFileContents(document)
    new_contents = old_contents.replace(".. code::\n", "::\n")

    # Add page counter reset right after TOC for PDF.
    new_contents = new_contents.replace(
        ".. contents::",
        """.. contents::

.. raw:: pdf

    PageBreak oneColumn
    SetPageCounter 1

""",
    )

    try:
        if new_contents != old_contents:
            document += ".tmp"
            putTextFileContents(filename=document, contents=new_contents)

        with withEnvironmentVarOverridden("PYTHONWARNINGS", "ignore"):
            check_call(["rst2pdf"] + args + [document])
    finally:
        if new_contents != old_contents:
            deleteFile(document, must_exist=False)

    deleteFile(style_filename, must_exist=True)

    assert os.path.exists(pdf_filename)

    return pdf_filename


def makeTable(grid):
    """Create a REST table."""

    def makeSeparator(num_cols, col_width, header_flag):
        if header_flag == 1:
            return num_cols * ("+" + (col_width) * "=") + "+\n"
        else:
            return num_cols * ("+" + (col_width) * "-") + "+\n"

    def normalizeCell(string, length):

        return string + ((length - len(string)) * " ")

    cell_width = 2 + max(
        functools.reduce(
            lambda x, y: x + y, [[len(item) for item in row] for row in grid], []
        )
    )
    num_cols = len(grid[0])
    rst = makeSeparator(num_cols, cell_width, 0)
    header_flag = 1
    for row in grid:
        rst = (
            rst
            + "| "
            + "| ".join([normalizeCell(x, cell_width - 1) for x in row])
            + "|\n"
        )
        rst = rst + makeSeparator(num_cols, cell_width, header_flag)
        header_flag = 0

    return rst
