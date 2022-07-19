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
""" Automatic formatting of Yaml files. """

import json
import sys
from collections import OrderedDict

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

from nuitka.utils.FileOperations import openTextFile
from nuitka.utils.Yaml import getYamlPackageConfigurationSchemaFilename

sys.setrecursionlimit(100000)

MASTER_KEYS = None
DATA_FILES_KEYS = None
DLLS_KEYS = None
DLLS_BY_CODE_KEYS = None
DLLS_FROM_FILENAMES_KEYS = None
ANTI_BLOAT_KEYS = None
IMPLICIT_IMPORTS_KEYS = None
OPTIONS_KEYS = None
OPTIONS_CHECKS_KEYS = None

YAML_HEADER = """---
# yamllint disable rule:line-length
# yamllint disable rule:indentation
# yamllint disable rule:comments-indentation
# too many spelling things, spell-checker: disable
"""

def _initNuitkaPackageSchema():
    # Singleton, pylint: disable=global-statement
    global MASTER_KEYS, DATA_FILES_KEYS, DLLS_KEYS, DLLS_BY_CODE_KEYS
    global DLLS_FROM_FILENAMES_KEYS, ANTI_BLOAT_KEYS, IMPLICIT_IMPORTS_KEYS
    global OPTIONS_KEYS, OPTIONS_CHECKS_KEYS

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


def _decideStrFormat(string):
    """
    take the character that is not closest to the beginning or end
    """
    # Singleton, pylint: disable=too-many-return-statements
    if (
        string not in MASTER_KEYS
        and string not in DATA_FILES_KEYS
        and string not in DLLS_KEYS
        and string not in DLLS_BY_CODE_KEYS
        and string not in DLLS_FROM_FILENAMES_KEYS
        and string not in ANTI_BLOAT_KEYS
        and string not in IMPLICIT_IMPORTS_KEYS
        and string not in OPTIONS_KEYS
        and string not in OPTIONS_CHECKS_KEYS
    ):
        single_quote_left = string.find("'")
        single_quote_right = string.rfind("'")
        quote_left = string.find('"')
        quote_right = string.rfind('"')

        if single_quote_left == -1 and not quote_left == -1:
            return "'"

        elif quote_left == -1 and not single_quote_left == -1:
            return '"'

        elif (
            single_quote_left == -1
            and single_quote_right == -1
            and quote_left == -1
            and quote_right == -1
        ):
            return '"'

        elif single_quote_left > quote_left and single_quote_right < quote_right:
            return "'"

        elif single_quote_left < quote_left and single_quote_right > quote_right:
            return '"'

        else:
            return '"'

    else:
        return ""


class CustomConstructor(ruamel.yaml.constructor.RoundTripConstructor):
    def construct_scalar(self, node):
        # Singleton, pylint: disable= too-many-branches,too-many-return-statements
        if not isinstance(node, ScalarNode):
            raise ConstructorError(
                None,
                None,
                _F("expected a scalar node, but found {node_id!s}", node_id=node.id),
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

            fss = FoldedScalarString(node.value.replace("\a", ""), anchor=node.anchor)
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


def formatYaml(path):
    """
    format and sort a yaml file
    """

    _initNuitkaPackageSchema()

    ruamel.yaml.constructor.RoundTripConstructor = CustomConstructor

    yaml = YAML(typ="rt", pure=True)
    yaml.width = 100000000  # high value to not wrap lines
    yaml.indent = 2

    with openTextFile(path, "r", encoding="utf-8") as input_file:
        data = yaml.load(input_file.read())

    new_data = []
    for entry in data:
        sorted_entry = dict(
            OrderedDict(
                [(key, entry[key]) for key in MASTER_KEYS if key in entry.keys()]
            )
        )
        if "data-files" in sorted_entry:
            sorted_entry["data-files"] = dict(
                OrderedDict(
                    [
                        (key, entry["data-files"][key])
                        for key in DATA_FILES_KEYS
                        if key in entry["data-files"].keys()
                    ]
                )
            )

        if "dlls" in sorted_entry:
            for sub_entry in sorted_entry["dlls"]:
                sub_entry = dict(
                    OrderedDict(
                        [
                            (key, sub_entry[key])
                            for key in DLLS_KEYS
                            if key in sub_entry.keys()
                        ]
                    )
                )

        if "anti-bloat" in sorted_entry:
            for sub_entry in sorted_entry["anti-bloat"]:
                sub_entry = dict(
                    OrderedDict(
                        [
                            (key, sub_entry[key])
                            for key in ANTI_BLOAT_KEYS
                            if key in sub_entry.keys()
                        ]
                    )
                )

        if "implicit-imports" in sorted_entry:
            for sub_entry in sorted_entry["implicit-imports"]:
                sub_entry = dict(
                    OrderedDict(
                        [
                            (key, sub_entry[key])
                            for key in IMPLICIT_IMPORTS_KEYS
                            if key in sub_entry.keys()
                        ]
                    )
                )

        if "options" in sorted_entry:
            for sub_entry in sorted_entry["options"]["checks"]:
                sub_entry = dict(
                    OrderedDict(
                        [
                            (key, sub_entry[key])
                            for key in OPTIONS_CHECKS_KEYS
                            if key in sub_entry.keys()
                        ]
                    )
                )

        new_data.append(sorted_entry)

    # Do not sort by name yet, not clear if ever.
    # new_data = sorted(new_data, key=lambda d: d["module-name"].lower())

    with open(path, "w", encoding="utf-8") as output_file:
        output_file.write(YAML_HEADER)
        yaml.dump(new_data, output_file)
