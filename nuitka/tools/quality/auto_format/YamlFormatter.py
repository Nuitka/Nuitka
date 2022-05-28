import json
import os
from collections import OrderedDict
from copy import copy

import yaml

with open(os.path.join(".vscode", "nuitka-package-config-schema.json")) as schema_file:
    schema = json.load(schema_file)

MASTER_KEYS = list(schema["items"]["properties"].keys())
DATA_FILES_KEYS = list(
    schema["items"]["properties"]["data-files"]["items"]["properties"].keys()
)
DLLS_KEYS = list(schema["items"]["properties"]["dlls"]["items"]["properties"].keys())
ANTI_BLOAT_KEYS = list(
    schema["items"]["properties"]["anti-bloat"]["items"]["properties"].keys()
)
IMPLICIT_IMPORTS_KEYS = list(
    schema["items"]["properties"]["implicit-imports"]["items"]["properties"].keys()
)
del schema


class _MyDumper(yaml.SafeDumper):
    def write_line_break(self, data=None):
        super().write_line_break(data)
        if len(self.indents) == 1:
            super().write_line_break()


def _strPresenter(dumper, data):
    if data.count("\n") > 0:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')

    return dumper.represent_scalar(
        'tag:yaml.org,2002:str',
        data,
        style='"'
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


def _getBetweenComments(lines: list, comments: dict):
    new_lines = copy(lines)
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


def _getEndOfLineComment(lines: list, comments: dict):
    # sourcery skip: use-fstring-for-concatenation
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


def _getComments(lines: list):
    lines, comments = _getOnTopComments(lines)
    lines, comments = _getBetweenComments(lines, comments)
    comments = _getEndOfLineComment(lines, comments)
    return comments


def _restoreComments(lines: list, comments: dict):
    # sourcery skip: use-fstring-for-concatenation
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
    yaml.add_representer(str, _strPresenter)
    yaml.representer.SafeRepresenter.add_representer(str, _strPresenter)
    with open(path, encoding="utf-8") as f:
        data = yaml.load(f, Loader=yaml.SafeLoader)
        f.seek(0)
        lines = f.read().splitlines()
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

    new_data = sorted(new_data, key=lambda d: d["module-name"].lower())

    with open(path, "w", encoding="utf-8") as f:
        dumped = yaml.dump(new_data, Dumper=_MyDumper, width=10000000, sort_keys=False)
        f.writelines(line + "\n" for line in header)
        f.writelines(
            line + "\n" for line in _restoreComments(dumped.splitlines(), comments)
        )
