#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Stage changes in Nuitka-Watch automatically

This aims at recognizing unimportant changes automatically and is used
for larger report format migrations in the future potentially.
"""

from nuitka.options.CommandLineOptionsTools import makeOptionsParser
from nuitka.tools.quality.Git import (
    getCheckoutFileChangeDesc,
    getFileHashContent,
    putFileHashContent,
    updateGitFile,
)
from nuitka.TreeXML import convertStringToXML, convertXmlToString
from nuitka.utils.FileOperations import getFileContents, withTemporaryFile

options = None


# This is XML API, spell-checker: ignore addprevious,getnext,addnext


def _findMatchingChild(current, node):
    node_tag = node.tag

    if node_tag == "module":
        attrib_name = "name"
    elif node_tag == "optimization-time":
        attrib_name = "pass"
    elif node_tag == "code-generation-time":
        attrib_name = None
    else:
        assert False, (node, current)

    if attrib_name is not None:
        attrib_value = node.attrib[attrib_name]

    for candidate in current.findall(node_tag):
        if attrib_name is not None:
            try:
                candidate_value = candidate.attrib[attrib_name]
            except KeyError:
                assert False, current

            if candidate_value == attrib_value:
                return candidate
        else:
            return candidate

    return None


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
        current = _findMatchingChild(current, node)

        if current is None:
            return None

    return current


def _acceptOptimizationTimeChanges(old_report, new_report):
    changed = False

    for new_node in new_report.xpath("//module/optimization-time"):
        old_node = findMatchingNode(old_report, new_node)

        if old_node is not None:
            old_node.getparent().replace(old_node, new_node)
            changed = True

    for new_node in new_report.xpath("//module/code-generation-time"):
        old_node = findMatchingNode(old_report, new_node)

        if old_node is not None:
            old_node.getparent().replace(old_node, new_node)
            changed = True
        else:
            parent_module = findMatchingNode(old_report, new_node.getparent())

            if parent_module is not None:
                optimization_times = parent_module.findall("optimization-time")

                if optimization_times:
                    parent_module.insert(
                        parent_module.index(optimization_times[-1]) + 1, new_node
                    )
                else:
                    parent_module.append(new_node)

                changed = True

    return changed


def _acceptDllOrderChanges(old_report, new_report):
    changed = False

    processed_parents = set()
    for new_dll in new_report.xpath("//included_dll"):
        new_parent = new_dll.getparent()
        if new_parent in processed_parents:
            continue
        processed_parents.add(new_parent)

        old_parent = findMatchingNode(old_report, new_parent)

        if old_parent is None:
            continue

        last_node = None
        used_old_nodes = set()

        for new_node in new_parent.findall("included_dll"):
            old_node = None
            for candidate in old_parent.findall("included_dll"):
                if candidate in used_old_nodes:
                    continue

                if candidate.attrib == new_node.attrib:
                    old_node = candidate
                    used_old_nodes.add(old_node)
                    break

            if old_node is not None:
                if last_node is None:
                    first_existing = old_parent.find("included_dll")
                    if first_existing is not None and first_existing != old_node:
                        first_existing.addprevious(old_node)
                        changed = True
                else:
                    if last_node.getnext() != old_node:
                        last_node.addnext(old_node)
                        changed = True

                last_node = old_node

    return changed


def onCompilationReportChange(filename, git_stage):
    print("Working on", filename)

    new_report = convertStringToXML(getFileContents(filename, mode="rb"), use_lxml=True)
    old_git_contents = getFileHashContent(git_stage["src_hash"])

    old_report = convertStringToXML(old_git_contents, use_lxml=True)

    new_nuitka_version = new_report.attrib["nuitka_version"]
    changed = False
    if old_report.attrib["nuitka_version"] != new_nuitka_version:
        old_report.attrib["nuitka_version"] = new_nuitka_version

        changed = True

    if options.accept_optimization_time:
        changed = changed | _acceptOptimizationTimeChanges(old_report, new_report)

    if options.accept_dll_order:
        changed = changed | _acceptDllOrderChanges(old_report, new_report)

    if changed:
        new_git_contents = convertXmlToString(old_report)
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

    parser = makeOptionsParser(usage=None, epilog=None)

    parser.add_option(
        "--accept-optimization-time",
        action="store_true",
        dest="accept_optimization_time",
        default=False,
        help="""Accept module optimization-time and code-generation-time changes.""",
    )

    # TODO: Once the sorting in reports is done, remove this option again.
    parser.add_option(
        "--accept-dll-order",
        action="store_true",
        dest="accept_dll_order",
        default=False,
        help="""Accept DLL order changes.""",
    )

    options, _positional_args = parser.parse_args()

    for git_stage in getCheckoutFileChangeDesc(staged=False):
        onFileChange(git_stage=git_stage)


if __name__ == "__main__":
    main()

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
