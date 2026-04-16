#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Utility module for generating diffs.

This wraps difflib to keep all diffing logic centralized and isolated.
"""

# spell-checker: ignore lineterm,tofile,fromlines,tolines,fromdesc,todesc,numlines

import difflib
import os

from .FileOperations import getFileContents, listDir


def getUnifiedDiff(
    old_lines, new_lines, old_filename, new_filename, num_lines=3, lineterm="\n"
):
    """Generate a unified diff from sequences of lines."""
    return difflib.unified_diff(
        a=old_lines,
        b=new_lines,
        fromfile=old_filename,
        tofile=new_filename,
        n=num_lines,
        lineterm=lineterm,
    )


def getHtmlDiffTable(
    old_lines, new_lines, old_desc, new_desc, context=False, num_lines=5
):
    """Generate an HTML diff table from sequences of lines."""
    return difflib.HtmlDiff().make_table(
        fromlines=old_lines,
        tolines=new_lines,
        fromdesc=old_desc,
        todesc=new_desc,
        context=context,
        numlines=num_lines,
    )


def compareDirectories(
    logger,
    my_print,
    dir1,
    dir2,
    ignore_suffixes=None,
    ignore_substrings=None,
):
    """Compare directories recursively."""
    # Many details and cases to deal with
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements

    if ignore_suffixes is None:
        ignore_suffixes = ()
    else:
        ignore_suffixes = tuple(ignore_suffixes)

    if ignore_substrings is None:
        ignore_substrings = ()
    else:
        ignore_substrings = tuple(ignore_substrings)

    done = set()
    result = False

    for path1, filename in listDir(dir1):
        if any(substr in path1 for substr in ignore_substrings):
            continue

        path2 = os.path.join(dir2, filename)
        done.add(path1)

        if filename.endswith(ignore_suffixes):
            continue

        if any(substr in filename for substr in ignore_substrings):
            continue

        if not os.path.exists(path2):
            logger.warning("Only in %s: %s" % (dir1, filename))
            result = False
            continue

        if os.path.isdir(path1):
            r = compareDirectories(
                logger=logger,
                my_print=my_print,
                dir1=path1,
                dir2=path2,
                ignore_suffixes=ignore_suffixes,
                ignore_substrings=ignore_substrings,
            )
            if r:
                result = True
        elif os.path.isfile(path1):
            if str is bytes:
                content1 = getFileContents(path1, mode="rb")
                content2 = getFileContents(path2, mode="rb")
            else:
                content1 = getFileContents(path1, encoding="latin1")
                content2 = getFileContents(path2, encoding="latin1")

            diff = getUnifiedDiff(
                old_lines=content1.splitlines(),
                new_lines=content2.splitlines(),
                old_filename=path1,
                new_filename=path2,
                num_lines=3,
            )

            diff_list = list(diff)

            if diff_list:
                for line in diff_list:
                    try:
                        my_print(line)
                    except UnicodeEncodeError:
                        my_print(repr(line))

                result = True
        else:
            assert False, path1

    for path2, filename in listDir(dir2):
        if any(substr in path2 for substr in ignore_substrings):
            continue

        path1 = os.path.join(dir1, filename)

        if path1 in done:
            continue

        if not os.path.exists(path1):
            logger.warning("Only in %s: %s" % (dir2, filename))
            result = False
            continue

    return result


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
