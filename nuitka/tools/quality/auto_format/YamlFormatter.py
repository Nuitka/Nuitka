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
import os
from collections import OrderedDict
from copy import copy

import yaml

from nuitka.utils.FileOperations import openTextFile

with openTextFile(
    os.path.join(".vscode", "nuitka-package-config-schema.json"), "r"
) as schema_file:
    schema = json.load(schema_file)

MASTER_KEYS = tuple(schema["items"]["properties"].keys())
DATA_FILES_KEYS = tuple(
    schema["items"]["properties"]["data-files"]["items"]["properties"].keys()
)
DLLS_KEYS = tuple(schema["items"]["properties"]["dlls"]["items"]["properties"].keys())
ANTI_BLOAT_KEYS = tuple(
    schema["items"]["properties"]["anti-bloat"]["items"]["properties"].keys()
)
IMPLICIT_IMPORTS_KEYS = tuple(
    schema["items"]["properties"]["implicit-imports"]["items"]["properties"].keys()
)
del schema


class _IndentingDumper(yaml.SafeDumper):
    """
    Custom dumper enforcing indentation.
    """

    def write_line_break(self, data=None):
        super(_IndentingDumper, self).write_line_break(data)
        if len(self.indents) == 1:
            super(_IndentingDumper, self).write_line_break()

    def increase_indent(self, flow=False, indentless=False):
        return super(_IndentingDumper, self).increase_indent(flow, False)


def _decideStrFormat(string: str):
    """
    take the character that is not closest to the beginning or end
    """
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


def _testDecideStrFormat():
    assert _decideStrFormat("") == '"'
    assert _decideStrFormat("'") == '"'
    assert _decideStrFormat('"') == "'"
    assert _decideStrFormat(""" '" """) == '"'
    assert _decideStrFormat(""" "'" """) == "'"
    assert _decideStrFormat(""" '"' """) == '"'


def _strPresenter(dumper, data):
    """
    custom Representer for strings
    """
    if data.count("\n") > 0:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')

    return dumper.represent_scalar(
        'tag:yaml.org,2002:str',
        data,
        style=_decideStrFormat(data)
        if (
            data not in MASTER_KEYS
            and data not in DATA_FILES_KEYS
            and data not in DLLS_KEYS
            and data not in ANTI_BLOAT_KEYS
            and data not in IMPLICIT_IMPORTS_KEYS
        )
        else '',
    )


def _getOnTopComments(lines: list):
    """
    find comments that are at the top
    example:
    # comment
    - module-name: "module"
    """
    comments = {}
    new_lines = copy(lines)
    deleted_counter = 0
    for i, line in enumerate(lines):
        error = False
        if line.startswith("#"):
            line2 = line
            counter = 0
            while not line2.startswith("- module-name: "):
                counter += 1
                line2 = lines[i + counter].strip()
                if len(line2) > 0 and line2[0] not in ["#", " ", "-"]:
                    error = True
                    break

            if error:
                continue

            module_name = line2.replace("- module-name: ", "")

            data = {"comment": line, "type": "on-top"}
            if module_name in comments:
                comments[module_name].append(data)

            else:
                comments[module_name] = [data]

            del new_lines[i - deleted_counter]
            deleted_counter += 1

    return new_lines, comments


def _getBetweenComments(lines, comments):
    """
    find comments between to lines
    example:
    - module-name: "arcade"
      # comment
      data-files:
    """
    for i, line in enumerate(lines):
        if line.strip().startswith("#"):
            comment = line
            line2 = line
            counter = 0
            while True:
                counter += 1
                line2 = lines[i - counter]
                if line2 != "" and not line2.strip().startswith("#"):
                    key = line2.strip()
                    break

            counter = 0
            while True:
                counter += 1
                line2 = lines[i - counter]
                if line2.startswith("- module-name: "):
                    module_name = line2.replace("- module-name: ", "")
                    break

            del lines[i]

            data = {"key": key, "comment": comment, "type": "between"}
            if module_name in comments:
                comments[module_name].append(data)

            else:
                comments[module_name] = [data]

    return lines, comments


def _getEndOfLineComment(lines, comments):
    """
    find comments at the end of a line
    example:
    - "module" # comment
    """
    for i, line in enumerate(lines):
        splitted_line = line.split("#")
        if len(splitted_line) > 1:
            comment = "#" + splitted_line[-1]
            key = "".join(splitted_line[:-1]).strip()
            line2 = line
            counter = 0
            while True:
                counter += 1
                line2 = lines[i - counter]
                if line2.startswith("- module-name: "):
                    module_name = line2.replace("- module-name: ", "")
                    break

            data = {"key": key, "comment": comment, "type": "on-end"}

            if module_name in comments:
                comments[module_name].append(data)

            else:
                comments[module_name] = [data]

    return comments


def _getComments(lines):
    """
    find all comments using three parses
    """
    lines, comments = _getOnTopComments(lines)
    lines, comments = _getBetweenComments(lines, comments)
    comments = _getEndOfLineComment(lines, comments)
    return comments


def _restoreComments(lines, comments):
    """
    restore all comments from "comments"
    """
    new_lines = copy(lines)
    new_lines_counter = 0
    for i, line in enumerate(lines):
        if line.startswith("- module-name: "):
            module_name = line.split(": ")[1]
            if module_name in comments:
                for entry in comments[module_name]:
                    if entry["type"] == "on-top":
                        new_lines.insert(i + new_lines_counter, entry["comment"])

                        new_lines_counter += 1

                    if entry["type"] == "between":
                        line2 = line
                        counter = 0
                        while line2.strip() != entry["key"]:
                            counter += 1
                            line2 = lines[i + counter]

                        new_lines.insert(
                            i + counter + new_lines_counter + 1, entry["comment"]
                        )
                        new_lines_counter += 1

                    if entry["type"] == "on-end":
                        line2 = line
                        counter = 0
                        while line2.strip() != entry["key"]:
                            counter += 1
                            line2 = lines[i + counter]

                        new_lines[i + counter + new_lines_counter] = (
                            lines[i + counter] + " " + entry["comment"]
                        )

    return new_lines


def formatYaml(path):
    """
    format and sort a yaml file
    """
    yaml.add_representer(str, _strPresenter)
    yaml.representer.SafeRepresenter.add_representer(str, _strPresenter)

    with openTextFile(path, "r", encoding="utf-8") as input_file:
        data = yaml.load(input_file, Loader=yaml.SafeLoader)
        input_file.seek(0)
        lines = input_file.read().splitlines()
        header = lines[:3]
        comments = _getComments(lines[3:])

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
            sorted_entry["implicit-imports"] = dict(
                OrderedDict(
                    [
                        (key, entry["implicit-imports"][key])
                        for key in IMPLICIT_IMPORTS_KEYS
                        if key in entry["implicit-imports"].keys()
                    ]
                )
            )

        new_data.append(sorted_entry)

    # TODO: Do not sort by name yet.
    # new_data = sorted(new_data, key=lambda d: d["module-name"].lower())

    with openTextFile(path, "w", encoding="utf-8") as output_file:
        dumped = yaml.dump(
            new_data, Dumper=_IndentingDumper, width=10000000, sort_keys=False
        )

        output_file.writelines(line + "\n" for line in header)
        output_file.writelines(
            line + "\n" for line in _restoreComments(dumped.splitlines(), comments)
        )


_testDecideStrFormat()
