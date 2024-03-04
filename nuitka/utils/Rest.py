#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Work with ReST documentations.

This e.g. creates PDF documentations during release and tables from data
for the web site, e.g. downloads.

"""

import functools


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
