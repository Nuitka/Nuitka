#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Stage changes in Nuitka-Watch automatically

This aims at recognizing unimportant changes automatically and is used
for larger report format migrations in the future potentially.
"""

from nuitka.__past__ import StringIO
from nuitka.options.CommandLineOptionsTools import makeOptionsParser
from nuitka.tools.quality.Git import (
    getCheckoutFileChangeDesc,
    getFileHashContent,
    putFileHashContent,
    updateFileIndex,
)
from nuitka.TreeXML import convertStringToXML, convertXmlToString
from nuitka.utils.FileOperations import getFileContents, withTemporaryFile
from nuitka.utils.Json import (
    loadJsonFromContents,
    loadJsonFromFilename,
    writeJsonToFile,
)

options = None


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
            new_node.tail = old_node.tail
            old_node.getparent().replace(old_node, new_node)
            changed = True

    for new_node in new_report.xpath("//module/code-generation-time"):
        old_node = findMatchingNode(old_report, new_node)

        if old_node is not None:
            new_node.tail = old_node.tail
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


def _acceptModuleUsageChanges(old_report, new_report):
    """Accept module usage changes of modules present in both reports.

    Usages of updated package sources may be added, removed, re-ordered
    or change line numbers. Newly added and removed modules themselves
    are left for review in the working tree.
    """
    changed = False

    old_modules = {}
    for node in old_report.xpath("//module"):
        old_modules[node.attrib["name"]] = node

    for new_module in new_report.xpath("//module"):
        old_module = old_modules.get(new_module.attrib["name"])

        if old_module is None:
            continue

        old_usages = old_module.find("module_usages")
        new_usages = new_module.find("module_usages")

        if old_usages is None or new_usages is None:
            continue

        if [node.attrib for node in old_usages] == [node.attrib for node in new_usages]:
            continue

        new_usages.tail = old_usages.tail
        old_module.replace(old_usages, new_usages)
        changed = True

    return changed


def _acceptDistributionVersionBumps(old_report, new_report):
    """Accept version bumps of distributions present in both reports.

    Newly added distributions are left for review in the working tree.
    """
    changed = False

    old_distributions = {}
    for node in old_report.xpath("//distributions/distribution"):
        old_distributions[node.attrib["name"]] = node

    for new_node in new_report.xpath("//distributions/distribution"):
        old_node = old_distributions.get(new_node.attrib["name"])

        # Newly added distributions are not accepted, they are to be seen
        # as a result of the update.
        if old_node is None:
            continue

        if "version" not in old_node.attrib or "version" not in new_node.attrib:
            continue

        if old_node.attrib["version"] == new_node.attrib["version"]:
            continue

        old_attrib = dict(old_node.attrib)
        new_attrib = dict(new_node.attrib)
        old_attrib.pop("version")
        new_attrib.pop("version")

        if old_attrib != new_attrib:
            continue

        new_node.tail = old_node.tail
        old_node.getparent().replace(old_node, new_node)
        changed = True

    return changed


def _acceptDataFileSizeChanges(old_report, new_report):
    """Accept size changes of data files present in both reports.

    Newly added data files are left for review in the working tree.
    """
    changed = False

    old_data_files = {}
    for node in old_report.xpath("//data_file"):
        old_data_files.setdefault(node.attrib["name"], []).append(node)

    for new_node in new_report.xpath("//data_file"):
        if "size" not in new_node.attrib:
            continue

        candidates = old_data_files.get(new_node.attrib["name"])

        # Newly added data files are not accepted, they are to be seen as
        # a result of the update.
        if not candidates:
            continue

        new_attrib = dict(new_node.attrib)
        new_attrib.pop("size")

        for old_node in candidates:
            if "size" not in old_node.attrib:
                continue

            if old_node.attrib["size"] == new_node.attrib["size"]:
                continue

            old_attrib = dict(old_node.attrib)
            old_attrib.pop("size")

            if old_attrib != new_attrib:
                continue

            new_node.tail = old_node.tail
            old_node.getparent().replace(old_node, new_node)
            candidates.remove(old_node)
            changed = True
            break

    return changed


def _acceptPipenvHashChanges(old_report, new_report):
    """Accept pipenv hash changes and update the command line accordingly.

    Returns:
        True if a pipenv hash change was accepted, False otherwise.
    """
    new_hash = new_report.find(".//pipenv_hash")
    old_hash = old_report.find(".//pipenv_hash")

    if new_hash is None or old_hash is None or old_hash.text == new_hash.text:
        return False

    old_hash.text = new_hash.text

    for option_node in old_report.xpath("//command_line/option"):
        value = option_node.get("value")

        if value is not None and value.startswith(
            "--report-user-provided=pipenv_hash="
        ):
            option_node.set(
                "value",
                "--report-user-provided=pipenv_hash=%s" % new_hash.text,
            )

    return True


def _acceptPyPIChanges(old_report, new_report):
    """Accept distribution version bumps, data file size changes and pipenv
    hash changes.

    Newly added and removed distributions and data files are left for
    review in the working tree.
    """
    changed = _acceptDistributionVersionBumps(old_report, new_report)
    changed = changed | _acceptDataFileSizeChanges(old_report, new_report)
    changed = changed | _acceptPipenvHashChanges(old_report, new_report)
    changed = changed | _acceptModuleUsageChanges(old_report, new_report)

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

    if options.accept_pypi_bumps:
        changed = changed | _acceptPyPIChanges(old_report, new_report)

    if changed:
        new_git_contents = convertXmlToString(old_report, use_lxml=True)

        with withTemporaryFile(mode="wb", suffix=".xml", delete=False) as output_file:
            tmp_filename = output_file.name
            output_file.write(new_git_contents.encode("utf8"))
            output_file.close()

        new_hash_value = putFileHashContent(tmp_filename)

        if git_stage["src_hash"] != new_hash_value:
            updateFileIndex(git_stage, new_hash_value)


def onFileChange(git_stage):
    filename = git_stage["src_path"]

    if filename.endswith("compilation-report.xml"):
        onCompilationReportChange(filename=filename, git_stage=git_stage)
    elif options.accept_pypi_bumps and filename.endswith("Pipfile.lock"):
        onPipfileLockChange(filename=filename, git_stage=git_stage)


def _isPackageVersionBump(old_entry, new_entry):
    """Is the package entry change nothing but a version bump.

    The hashes and markers derived from the version may change along with
    it, but nothing else may.
    """
    if old_entry.get("version") == new_entry.get("version"):
        return False

    if "version" not in old_entry or "version" not in new_entry:
        return False

    for key in set(old_entry) | set(new_entry):
        if key in ("version", "hashes", "markers"):
            continue

        if old_entry.get(key) != new_entry.get(key):
            return False

    return True


def _acceptPipfileVersionBumps(old_lock, new_lock):
    """Accept version bumps of existing packages in all Pipfile.lock sections.

    Newly added packages are left for review in the working tree.

    Returns:
        Names of the packages that were accepted.
    """
    accepted = []

    for section_name in ("default", "develop"):
        old_section = old_lock.get(section_name)
        new_section = new_lock.get(section_name)

        if old_section is None or new_section is None:
            continue

        for package_name, new_entry in new_section.items():
            old_entry = old_section.get(package_name)

            # Newly added packages are not accepted, they are to be seen
            # as a result of the update.
            if old_entry is None:
                continue

            if _isPackageVersionBump(old_entry, new_entry):
                old_section[package_name] = new_entry
                accepted.append(package_name)

    return accepted


def onPipfileLockChange(filename, git_stage):
    """Accept version bumps of existing packages in a Pipfile.lock.

    Newly added and removed packages, as well as any other changes, are
    left for review in the working tree.
    """
    new_lock = loadJsonFromFilename(filename)
    old_lock = loadJsonFromContents(getFileHashContent(git_stage["src_hash"]))

    accepted = _acceptPipfileVersionBumps(old_lock, new_lock)

    if not accepted:
        return

    print(
        "Working on %s: accepting %d package version bumps." % (filename, len(accepted))
    )

    output = StringIO()
    writeJsonToFile(output, old_lock, indent=4)

    with withTemporaryFile(mode="wb", suffix=".lock", delete=False) as output_file:
        tmp_filename = output_file.name
        output_file.write(output.getvalue().encode("utf8"))
        output_file.close()

    new_hash_value = putFileHashContent(tmp_filename)

    if git_stage["src_hash"] != new_hash_value:
        updateFileIndex(git_stage, new_hash_value)


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

    parser.add_option(
        "--accept-pypi-bumps",
        action="store_true",
        dest="accept_pypi_bumps",
        default=False,
        help="""Accept package version bumps in Pipfile.lock files, but keep newly
added and removed packages in the diff.""",
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
