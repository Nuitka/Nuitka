#     Copyright 2022, Fire-Cube <ben7@gmx.ch>
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
""" Automatic formatting of Yaml files.

spell-checker: ignore ruamel, scalarstring
"""

import json
import sys

from nuitka.__past__ import StringIO
from nuitka.Tracing import tools_logger
from nuitka.utils.FileOperations import (
    getFileContents,
    openTextFile,
    renameFile,
)
from nuitka.utils.Yaml import (
    PackageConfigYaml,
    getYamlPackageConfigurationSchemaFilename,
    parseYaml,
)

MASTER_KEYS = None
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
# too many spelling things, spell-checker: disable
"""


def _initNuitkaPackageSchema():
    # Singleton, pylint: disable=global-statement
    global MASTER_KEYS, DATA_FILES_KEYS, DLLS_KEYS, DLLS_BY_CODE_KEYS
    global DLLS_FROM_FILENAMES_KEYS, ANTI_BLOAT_KEYS, IMPLICIT_IMPORTS_KEYS
    global OPTIONS_KEYS, OPTIONS_CHECKS_KEYS, IMPORT_HACK_KEYS

    with openTextFile(
        getYamlPackageConfigurationSchemaFilename(),
        "r",
    ) as schema_file:
        schema = json.load(schema_file)

    MASTER_KEYS = tuple(schema["items"]["properties"].keys())
    DATA_FILES_KEYS = tuple(
        schema["items"]["properties"]["data-files"]["properties"].keys()
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
    """
    take the character that is not closest to the beginning or end
    """
    # Singleton, pylint: disable=too-many-return-statements
    if (
        string_value not in MASTER_KEYS
        and string_value not in DATA_FILES_KEYS
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
    import ruamel

    # Yes, friends with ruamel here, to make a sorted copy
    # pylint: disable=protected-access

    result = ruamel.yaml.comments.CommentedMap()
    for key, value in sorted(
        entry._items(),
        key=lambda item: key_order.index(item[0]) if item[0] in key_order else 1000,
    ):
        result[key] = value

        # Strip trailing new lines from end of sequence. It is attached to
        # the last key.
        if type(value) is ruamel.yaml.comments.CommentedMap and value.items():
            sub_mapping_key, _submapping_value = list(value._items())[-1]

            if sub_mapping_key in value.ca.items:
                ca_value = value.ca.items[sub_mapping_key]

                if type(ca_value[2]) is ruamel.yaml.tokens.CommentToken:
                    ca_value[2]._value = ca_value[2]._value.rstrip() + "\n"

    entry.copy_attributes(result)

    return result


def _reorderDictionaryList(entry_list, key_order):
    import ruamel

    result = ruamel.yaml.comments.CommentedSeq()
    result.extend(_reorderDictionary(entry, key_order) for entry in entry_list)

    for attribute_name in entry_list.ca.__slots__:
        setattr(result.ca, attribute_name, getattr(entry_list.ca, attribute_name))

    return result


def deepCompareYamlFiles(path1, path2):
    yaml1 = PackageConfigYaml(path1, parseYaml(getFileContents(path1)))
    yaml2 = PackageConfigYaml(path2, parseYaml(getFileContents(path2)))

    import deepdiff

    diff = deepdiff.diff.DeepDiff(yaml1.items(), yaml2.items(), ignore_order=True)

    return diff


def formatYaml(path):
    """
    format and sort a yaml file
    """
    # local on purpose, so no imports are deferred, and complex code
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements

    sys.setrecursionlimit(100000)

    _initNuitkaPackageSchema()

    import ruamel
    from ruamel.yaml import YAML
    from ruamel.yaml.compat import _F
    from ruamel.yaml.constructor import ConstructorError
    from ruamel.yaml.nodes import ScalarNode
    from ruamel.yaml.scalarstring import (
        DoubleQuotedScalarString,
        FoldedScalarString,
        LiteralScalarString,
        PlainScalarString,
        SingleQuotedScalarString,
    )

    class CustomConstructor(ruamel.yaml.constructor.RoundTripConstructor):
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

    ruamel.yaml.constructor.RoundTripConstructor = CustomConstructor

    yaml = YAML(typ="rt", pure=True)
    yaml.width = 100000000  # high value to not wrap lines
    yaml.explicit_start = True
    yaml.indent(sequence=4, offset=2)

    data = yaml.load(getFileContents(path))

    new_data = []
    for entry in data:
        sorted_entry = _reorderDictionary(entry, MASTER_KEYS)

        if "data-files" in sorted_entry:
            sorted_entry["data-files"] = _reorderDictionary(
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

        lastline = None
        for line in string_io.getvalue().splitlines():
            # Duplicate new-lines are a no-go.
            if lastline == "" and line == "":
                continue

            if line.startswith("  "):
                if not line.lstrip().startswith("#"):
                    line = line[2:]

            if line.startswith("- module-name:"):
                if (
                    lastline != ""
                    and not lastline.startswith("#")
                    and not lastline == "---"
                ):
                    output_file.write("\n")

            lastline = line

            output_file.write(line + "\n")

    diff = deepCompareYamlFiles(path, tmp_path)
    if diff:
        tools_logger.sysexit(
            "Error, auto-format for Yaml file %s is changing contents %s" % (path, diff)
        )

    renameFile(tmp_path, path)
