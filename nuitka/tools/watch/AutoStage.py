#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Stage changes in Nuitka-Watch automatically

This aims at recognizing unimportant changes automatically and is used
for larger report format migrations in the future potentially.
"""

from nuitka.tools.quality.Git import (
    getCheckoutFileChangeDesc,
    getFileHashContent,
    putFileHashContent,
    updateGitFile,
)
from nuitka.TreeXML import fromString, toString
from nuitka.utils.FileOperations import getFileContents, withTemporaryFile


def onCompilationReportChange(filename, git_stage):
    new_report = fromString(getFileContents(filename))
    old_git_contents = getFileHashContent(git_stage["src_hash"])

    if str is not bytes:
        old_git_contents = old_git_contents.decode("utf8")

    old_report = fromString(old_git_contents)

    new_nuitka_version = new_report.attrib["nuitka_version"]
    changed = False
    if old_report.attrib["nuitka_version"] != new_nuitka_version:
        old_report.attrib["nuitka_version"] = new_nuitka_version

        changed = True

    if changed:
        new_git_contents = toString(old_report)
        with withTemporaryFile(mode="w", delete=False) as output_file:
            tmp_filename = output_file.name
            output_file.write(new_git_contents)
            output_file.close()

        new_hash_value = putFileHashContent(tmp_filename)

        updateGitFile(filename, git_stage["src_hash"], new_hash_value, staged=False)


def onFileChange(git_stage):
    filename = git_stage["src_path"]

    if filename.endswith("compilation-report.xml"):
        onCompilationReportChange(filename=filename, git_stage=git_stage)


def main():
    for git_stage in getCheckoutFileChangeDesc(staged=False):
        onFileChange(git_stage=git_stage)


if __name__ == "__main__":
    main()

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
