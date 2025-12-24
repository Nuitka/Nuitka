#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Automatic formatting of Yaml files.

spell-checker: ignore ruamel, scalarstring
"""

import json
import sys

from nuitka.__past__ import StringIO
from nuitka.utils.FileOperations import (
    getFileContents,
    openTextFile,
    renameFile,
)
from nuitka.utils.Yaml import (
    PackageConfigYaml,
    getDeepDiffPackage,
    getRuamelYamlPackage,
    getYamlPackageConfigurationSchemaFilename,
)

MASTER_KEYS = None
VARIABLE_KEYS = None
DATA_FILES_KEYS = None
DLLS_KEYS = None
DLLS_BY_CODE_KEYS = None
DLLS_FROM_FILENAMES_KEYS = None
ANTI_BLOAT_KEYS = None
IMPLICIT_IMPORTS_KEYS = None
OPTIONS_KEYS = None
OPTIONS_CHECKS_KEYS = None
IMPORT_HACK_KEYS = None

SINGLE_QUOTE = "'"
DOUBLE_QUOTE = '"'

YAML_HEADER = """\
# yamllint disable rule:line-length
# yamllint disable rule:indentation
# yamllint disable rule:comments-indentation
# yamllint disable rule:comments
# too many spelling things, spell-checker: disable
"""


def _initNuitkaPackageSchema():
    """Initialize the Nuitka package configuration schema."""
    # Singleton, pylint: disable=global-statement
    global MASTER_KEYS, VARIABLE_KEYS, DATA_FILES_KEYS, DLLS_KEYS, DLLS_BY_CODE_KEYS
    global DLLS_FROM_FILENAMES_KEYS, ANTI_BLOAT_KEYS, IMPLICIT_IMPORTS_KEYS
    global OPTIONS_KEYS, OPTIONS_CHECKS_KEYS, IMPORT_HACK_KEYS

    with openTextFile(
        getYamlPackageConfigurationSchemaFilename(),
        "r",
    ) as schema_file:
        schema = json.load(schema_file)

    MASTER_KEYS = tuple(schema["items"]["properties"].keys())
    VARIABLE_KEYS = tuple(
        schema["items"]["properties"]["variables"]["properties"].keys()
    )
    DATA_FILES_KEYS = tuple(
        schema["items"]["properties"]["data-files"]["items"]["properties"].keys()
    )
    DLLS_KEYS = tuple(
        schema["items"]["properties"]["dlls"]["items"]["properties"].keys()
    )
    DLLS_BY_CODE_KEYS = tuple(
        schema["items"]["properties"]["dlls"]["items"]["properties"]["by_code"][
            "properties"
        ].keys()
    )
    DLLS_FROM_FILENAMES_KEYS = tuple(
        schema["items"]["properties"]["dlls"]["items"]["properties"]["from_filenames"][
            "properties"
        ].keys()
    )
    ANTI_BLOAT_KEYS = tuple(
        schema["items"]["properties"]["anti-bloat"]["items"]["properties"].keys()
    )
    IMPLICIT_IMPORTS_KEYS = tuple(
        schema["items"]["properties"]["implicit-imports"]["items"]["properties"].keys()
    )
    OPTIONS_KEYS = tuple(schema["items"]["properties"]["options"]["properties"].keys())
    OPTIONS_CHECKS_KEYS = tuple(
        schema["items"]["properties"]["options"]["properties"]["checks"]["items"][
            "properties"
        ].keys()
    )
    IMPORT_HACK_KEYS = tuple(
        schema["items"]["properties"]["import-hacks"]["items"]["properties"].keys()
    )


def _decideStrFormat(string_value):
    """Decide which string format to use for a given YAML string value.

    Args:
        string_value: str - string value to check

    Returns:
        str: SINGLE_QUOTE, DOUBLE_QUOTE or empty string (for plain)
    """
    # Singleton, pylint: disable=too-many-boolean-expressions,too-many-return-statements
    if (
        string_value not in MASTER_KEYS
        and string_value not in DATA_FILES_KEYS
        and string_value not in VARIABLE_KEYS
        and string_value not in DLLS_KEYS
        and string_value not in DLLS_BY_CODE_KEYS
        and string_value not in DLLS_FROM_FILENAMES_KEYS
        and string_value not in ANTI_BLOAT_KEYS
        and string_value not in IMPLICIT_IMPORTS_KEYS
        and string_value not in OPTIONS_KEYS
        and string_value not in IMPORT_HACK_KEYS
        and string_value not in OPTIONS_CHECKS_KEYS
    ):
        single_quote_left_pos = string_value.find("'")
        single_quote_right_pos = string_value.rfind("'")
        double_quote_left_pos = string_value.find('"')
        double_quote_right_pos = string_value.rfind('"')

        if single_quote_left_pos == -1 and not double_quote_left_pos == -1:
            return SINGLE_QUOTE

        elif double_quote_left_pos == -1 and not single_quote_left_pos == -1:
            return DOUBLE_QUOTE

        elif (
            single_quote_left_pos == -1
            and single_quote_right_pos == -1
            and double_quote_left_pos == -1
            and double_quote_right_pos == -1
        ):
            if "\n" in string_value:
                return DOUBLE_QUOTE
            else:
                return SINGLE_QUOTE

        elif (
            single_quote_left_pos > double_quote_left_pos
            and single_quote_right_pos < double_quote_right_pos
        ):
            return SINGLE_QUOTE

        else:
            return DOUBLE_QUOTE

    else:
        return ""


def _reorderDictionary(entry, key_order):
    """Reorder a dictionary based on a given key order.

    Args:
        entry: ruamel.yaml.comments.CommentedMap - dictionary to reorder
        key_order: tuple - keys in the desired order

    Returns:
        ruamel.yaml.comments.CommentedMap: reordered dictionary
    """
    ruamel_yaml = getRuamelYamlPackage(logger=None, assume_yes_for_downloads=True)

    # Yes, friends with ruamel here, to make a sorted copy
    # pylint: disable=protected-access

    result = ruamel_yaml.comments.CommentedMap()
    for key, value in sorted(
        entry._items(),
        key=lambda item: key_order.index(item[0]) if item[0] in key_order else 1000,
    ):
        result[key] = value

        # Strip trailing new lines from end of sequence. It is attached to
        # the last key.
        if type(value) is ruamel_yaml.comments.CommentedMap and value.items():
            sub_mapping_key, _submapping_value = list(value._items())[-1]

            if sub_mapping_key in value.ca.items:
                ca_value = value.ca.items[sub_mapping_key]

                if type(ca_value[2]) is ruamel_yaml.tokens.CommentToken:
                    ca_value[2]._value = ca_value[2]._value.rstrip() + "\n"

    entry.copy_attributes(result)

    return result


def _reorderDictionaryList(entry_list, key_order):
    """Reorder a list of dictionaries based on a given key order.

    Args:
        entry_list: ruamel.yaml.comments.CommentedSeq - list to reorder
        key_order: tuple - keys in the desired order

    Returns:
        ruamel.yaml.comments.CommentedSeq: list with reordered dictionaries
    """
    ruamel_yaml = getRuamelYamlPackage(logger=None, assume_yes_for_downloads=True)

    result = ruamel_yaml.comments.CommentedSeq()
    result.extend(_reorderDictionary(entry, key_order) for entry in entry_list)

    for attribute_name in entry_list.ca.__slots__:
        setattr(result.ca, attribute_name, getattr(entry_list.ca, attribute_name))

    return result


def deepCompareYamlFiles(logger, path1, path2, assume_yes_for_downloads):
    """Deeply compare two YAML files for equivalence using DeepDiff.

    Args:
        logger: logger to use
        path1: str - path to the first YAML file
        path2: str - path to the second YAML file
        assume_yes_for_downloads: if tools should be downloaded automatically

    Returns:
        deepdiff.DeepDiff object representing the differences
    """
    yaml1 = PackageConfigYaml(
        logger=logger,
        name=path1,
        file_data=getFileContents(filename=path1, mode="rb"),
        assume_yes_for_downloads=assume_yes_for_downloads,
        check_checksums=False,
    )
    yaml2 = PackageConfigYaml(
        logger=logger,
        name=path2,
        file_data=getFileContents(filename=path2, mode="rb"),
        assume_yes_for_downloads=assume_yes_for_downloads,
        check_checksums=False,
    )

    deepdiff = getDeepDiffPackage(
        logger=logger, assume_yes_for_downloads=assume_yes_for_downloads
    )

    diff = deepdiff.diff.DeepDiff(yaml1.items(), yaml2.items(), ignore_order=True)

    return diff


def formatYaml(logger, path, assume_yes_for_downloads, ignore_diff=False):
    """Format and sort a YAML file.

    Args:
        logger: logger to use
        path: str - path to the YAML file to format
        assume_yes_for_downloads: bool - if tools should be downloaded automatically
        ignore_diff: bool - if diff between original and formatted should be ignored
    """
    # local on purpose, so no imports are deferred, and complex code
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements

    sys.setrecursionlimit(100000)

    _initNuitkaPackageSchema()

    ruamel_yaml = getRuamelYamlPackage(
        logger=logger, assume_yes_for_downloads=assume_yes_for_downloads
    )
    YAML = ruamel_yaml.YAML
    _F = ruamel_yaml.compat._F  # pylint: disable=protected-access
    ConstructorError = ruamel_yaml.constructor.ConstructorError
    ScalarNode = ruamel_yaml.nodes.ScalarNode
    DoubleQuotedScalarString = ruamel_yaml.scalarstring.DoubleQuotedScalarString
    FoldedScalarString = ruamel_yaml.scalarstring.FoldedScalarString
    LiteralScalarString = ruamel_yaml.scalarstring.LiteralScalarString
    PlainScalarString = ruamel_yaml.scalarstring.PlainScalarString
    SingleQuotedScalarString = ruamel_yaml.scalarstring.SingleQuotedScalarString

    class CustomConstructor(ruamel_yaml.constructor.RoundTripConstructor):
        def construct_scalar(self, node):
            # foreign code , pylint: disable=too-many-branches,too-many-return-statements
            if not isinstance(node, ScalarNode):
                raise ConstructorError(
                    None,
                    None,
                    _F(
                        "expected a scalar node, but found {node_id!s}", node_id=node.id
                    ),
                    node.start_mark,
                )

            if node.style == "|" and isinstance(node.value, str):
                lss = LiteralScalarString(node.value, anchor=node.anchor)
                if self.loader and self.loader.comment_handling is None:
                    if node.comment and node.comment[1]:
                        lss.comment = node.comment[1][0]

                else:
                    if node.comment is not None and node.comment[1]:
                        lss.comment = self.comment(node.comment[1][0])

                return lss

            if node.style == ">" and isinstance(node.value, str):
                fold_positions = []
                idx = -1
                while True:
                    idx = node.value.find("\a", idx + 1)
                    if idx < 0:
                        break

                    fold_positions.append(idx - len(fold_positions))

                fss = FoldedScalarString(
                    node.value.replace("\a", ""), anchor=node.anchor
                )
                if self.loader and self.loader.comment_handling is None:
                    if node.comment and node.comment[1]:
                        fss.comment = node.comment[1][0]

                else:
                    # NEWCMNT
                    if node.comment is not None and node.comment[1]:
                        # nprintf('>>>>nc2', node.comment)
                        # EOL comment after >
                        fss.comment = self.comment(node.comment[1][0])  # type: ignore

                if fold_positions:
                    fss.fold_pos = fold_positions  # type: ignore

                return fss

            elif isinstance(node.value, str):
                node.style = _decideStrFormat(node.value)
                if node.style == "'":
                    return SingleQuotedScalarString(node.value, anchor=node.anchor)

                if node.style == '"':
                    return DoubleQuotedScalarString(node.value, anchor=node.anchor)

                if node.style == "":
                    return PlainScalarString(node.value, anchor=node.anchor)

            if node.anchor:
                return PlainScalarString(node.value, anchor=node.anchor)

            return node.value

    ruamel_yaml.constructor.RoundTripConstructor = CustomConstructor

    yaml = YAML(typ="rt", pure=True)
    yaml.width = 100000000  # high value to not wrap lines
    yaml.explicit_start = True
    yaml.indent(sequence=4, offset=2)

    file_data = getFileContents(path, mode="rb")

    data = yaml.load(file_data)

    new_data = []
    for entry in data:
        sorted_entry = _reorderDictionary(entry, MASTER_KEYS)

        if "data-files" in sorted_entry:
            sorted_entry["data-files"] = _reorderDictionaryList(
                entry["data-files"], DATA_FILES_KEYS
            )

        if "dlls" in sorted_entry:
            sorted_entry["dlls"] = _reorderDictionaryList(
                sorted_entry["dlls"], DLLS_KEYS
            )

        if "anti-bloat" in sorted_entry:
            sorted_entry["anti-bloat"] = _reorderDictionaryList(
                sorted_entry["anti-bloat"], ANTI_BLOAT_KEYS
            )

        if "implicit-imports" in sorted_entry:
            sorted_entry["implicit-imports"] = _reorderDictionaryList(
                sorted_entry["implicit-imports"], IMPLICIT_IMPORTS_KEYS
            )

        if "options" in sorted_entry:
            sorted_entry["options"]["checks"] = _reorderDictionaryList(
                sorted_entry["options"]["checks"], OPTIONS_CHECKS_KEYS
            )

        if "import-hacks" in sorted_entry:
            sorted_entry["import-hacks"] = _reorderDictionaryList(
                sorted_entry["import-hacks"], IMPORT_HACK_KEYS
            )

        new_data.append(sorted_entry)

    new_data = sorted(new_data, key=lambda d: d["module-name"].lower())

    tmp_path = path + ".tmp"

    with open(tmp_path, "w", encoding="utf-8") as output_file:
        output_file.write(YAML_HEADER)

        string_io = StringIO()
        yaml.dump(new_data, string_io)

        last_line = None
        pipe_block = False
        for line in string_io.getvalue().splitlines():
            # Duplicate new-lines are a no-go.
            if last_line == "" and line == "":
                continue

            if line.startswith("  "):
                if not line.lstrip().startswith("#") or pipe_block:
                    line = line[2:]

            if line.endswith("|"):
                pipe_block = True
                pipe_block_prefix = (len(line) - len(line.lstrip()) + 2) * " "
            elif pipe_block and not line.startswith(pipe_block_prefix):
                pipe_block = False

            if line.startswith("- module-name:"):
                if (
                    last_line != ""
                    and not last_line.startswith("#")
                    and not last_line == "---"
                ):
                    output_file.write("\n")

            last_line = line

            output_file.write(line + "\n")

    if not ignore_diff:
        diff = deepCompareYamlFiles(
            logger=logger,
            path1=path,
            path2=tmp_path,
            assume_yes_for_downloads=assume_yes_for_downloads,
        )
        if diff:
            if logger:
                return logger.sysexit(
                    "Error, auto-format for Yaml file %s is changing contents %s"
                    % (path, diff)
                )
            else:
                sys.exit(
                    "Error, auto-format for Yaml file %s is changing contents %s"
                    % (path, diff)
                )

    renameFile(tmp_path, path)


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
