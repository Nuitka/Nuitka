#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Stage changes in Nuitka-Watch automatically

This aims at recognizing unimportant changes automatically and is used
for larger report format migrations in the future potentially.
"""

from optparse import OptionParser

from nuitka.tools.quality.Git import (
    getCheckoutFileChangeDesc,
    getFileHashContent,
    putFileHashContent,
    updateGitFile,
)
from nuitka.TreeXML import fromString, toString
from nuitka.utils.FileOperations import getFileContents, withTemporaryFile

options = None


def findMatchingNode(root, search_node):
    """Find a node matching the given one in a XML root."""
    nodes = []

    node = search_node
    while node is not None:
        nodes.insert(0, node)

        node = node.getparent()

    # Root is easy and hard coded.
    current = root
    del nodes[0]

    for node in nodes:
        node_tag = node.tag

        if node_tag == "module":
            attrib_name = "name"
        elif node_tag == "optimization-time":
            attrib_name = "pass"
        else:
            assert False, (node, current)

        attrib_value = node.attrib[attrib_name]

        for candidate in current.findall(node_tag):
            try:
                candidate_value = candidate.attrib[attrib_name]
            except KeyError:
                assert False, current

            if candidate_value == attrib_value:
                current = candidate
                break
        else:
            return None

    return current


def onCompilationReportChange(filename, git_stage):
    print("Working on", filename)

    new_report = fromString(getFileContents(filename, mode="rb"), use_lxml=True)
    old_git_contents = getFileHashContent(git_stage["src_hash"])

    old_report = fromString(old_git_contents, use_lxml=True)

    new_nuitka_version = new_report.attrib["nuitka_version"]
    changed = False
    if old_report.attrib["nuitka_version"] != new_nuitka_version:
        old_report.attrib["nuitka_version"] = new_nuitka_version

        changed = True

    if options.accept_optimization_time:
        for new_node in new_report.xpath("//module/optimization-time"):
            old_node = findMatchingNode(old_report, new_node)

            if old_node is not None:
                old_node.getparent().replace(old_node, new_node)
                changed = True

    if changed:
        new_git_contents = toString(old_report)
        with withTemporaryFile(mode="w", delete=False) as output_file:
            tmp_filename = output_file.name
            output_file.write(new_git_contents)
            output_file.close()

        new_hash_value = putFileHashContent(tmp_filename)

        if git_stage["src_hash"] != new_hash_value:
            updateGitFile(filename, git_stage["src_hash"], new_hash_value, staged=False)


def onFileChange(git_stage):
    filename = git_stage["src_path"]

    if filename.endswith("compilation-report.xml"):
        onCompilationReportChange(filename=filename, git_stage=git_stage)


def main():
    # Cheating in this singleton and not passing options,
    # pylint: disable=global-statement
    global options

    parser = OptionParser()

    parser.add_option(
        "--accept-optimization-time",
        action="store_true",
        dest="accept_optimization_time",
        default=False,
        help="""Accept module optimization-time changes.""",
    )

    options, _positional_args = parser.parse_args()

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
