from collections import OrderedDict
from copy import copy
from pathlib import Path

import yaml

MASTER_KEYS = [
    "module-name",
    "data-files",
    "dlls",
    "anti-bloat",
    "implicit-imports"
]

DATA_FILES_KEYS = [
    "dirs",
    "patterns",
    "control_tags",
    "empty_dirs",
    "empty_dir_structures"
]

DLLS_KEYS = [
    "include_from_code",
    "setup_code",
    "dll_filename_code",
    "dest_path",
    "include_from_filenames",
    "dir",
    "patterns"
]

ANTI_BLOAT_KEYS = [
    "module_code",
    "description",
    "context",
    "control_tags",
    "replacements",
    "replacements_plain",
    "change_function"
]

IMPLICIT_IMPORTS_KEYS = [
    "depends",
    "standalone_macos_bundle_mode",
    "disable_console"
]

class MyDumper(yaml.SafeDumper):
    def write_line_break(self, data=None):
        super().write_line_break(data)
        if len(self.indents) == 1:
            super().write_line_break()

def str_presenter(dumper, data):
    if data.count("\n") > 0:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')

    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"' if (
        data not in MASTER_KEYS and
        data not in DATA_FILES_KEYS and
        data not in DLLS_KEYS and
        data not in ANTI_BLOAT_KEYS and
        data not in IMPLICIT_IMPORTS_KEYS)
        else '')

def get_on_top_comments(lines: list):
    comments = {}
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

            data = {
                "comment": line,
                "type": "on-top"
            }
            if module_name in comments:
                comments[module_name].append(data)

            else:
                comments[module_name] = [data]

            del lines[i]

    return lines, comments

def get_between_comments(lines: list, comments: dict):
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

            data = {
                    "key": key,
                    "comment": comment,
                    "type": "between"
            }
            if module_name in comments:
                comments[module_name].append(data)

            else:
                comments[module_name] = [data]

    return lines, comments

def get_end_of_line_comment(lines: list, comments: dict):
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

            data = {
                "key": key,
                "comment": comment,
                "type": "on-end"
            }

            if module_name in comments:
                comments[module_name].append(data)

            else:
                comments[module_name] = [data]

    return comments

def get_comments(lines: list):
    lines, comments = get_on_top_comments(lines)
    lines, comments = get_between_comments(lines, comments)
    comments = get_end_of_line_comment(lines, comments)
    return comments

def restore_comments(lines: list, comments: dict):
    # sourcery skip: use-fstring-for-concatenation
    new_lines = copy(lines)
    for i, line in enumerate(lines):
        if line.startswith("- module-name: "):
            module_name = line.split(": ")[1]
            if module_name in comments:
                for entry in comments[module_name]:
                    if entry["type"] == "on-top":
                        new_lines.insert(i, entry["comment"])

                    if entry["type"] == "between":
                        line2 = line
                        counter = 0
                        while line2.strip() != entry["key"]:
                            counter += 1
                            line2 = lines[i + counter]

                        new_lines.insert(i + counter + 1, entry["comment"])

                    if entry["type"] == "on-end":
                        line2 = line
                        counter = 0
                        while line2.strip() != entry["key"]:
                            counter += 1
                            line2 = lines[i + counter]

                        new_lines[i + counter + 1] = lines[i + counter] + " " + entry["comment"]

    return new_lines

def format_yaml(path):
    yaml.add_representer(str, str_presenter)
    yaml.representer.SafeRepresenter.add_representer(str, str_presenter)
    with open(path) as f:
        data = yaml.load(f, Loader=yaml.SafeLoader)
        f.seek(0)
        comments = get_comments(f.read().splitlines())

    new_data = []
    for entry in data:
        sorted_entry = dict(OrderedDict([(key, entry[key]) for key in MASTER_KEYS if key in entry.keys()]))
        if "data-files" in sorted_entry:
            sorted_entry["data-files"] = dict(OrderedDict([(key, entry["data-files"][key]) for key in DATA_FILES_KEYS if key in entry["data-files"].keys()]))

        if "dlls" in sorted_entry:
            for sub_entry in sorted_entry["dlls"]:
                sub_entry = dict(OrderedDict([(key, sub_entry[key]) for key in DLLS_KEYS if key in sub_entry.keys()]))

        if "anti-bloat" in sorted_entry:
            for sub_entry in sorted_entry["anti-bloat"]:
                sub_entry = dict(OrderedDict([(key, sub_entry[key]) for key in ANTI_BLOAT_KEYS if key in sub_entry.keys()]))

        if "implicit-imports" in sorted_entry:
            sorted_entry["implicit-imports"] = dict(OrderedDict([(key, entry["implicit-imports"][key]) for key in IMPLICIT_IMPORTS_KEYS if key in entry["implicit-imports"].keys()]))

        new_data.append(sorted_entry)

    new_data = sorted(new_data, key=lambda d: d["module-name"].lower())

    with open(path, "w") as f:
        dumped = yaml.dump(new_data, Dumper=MyDumper, width=10000000, sort_keys=False)
        f.writelines(line + "\n" for line in restore_comments(dumped.splitlines(), comments))