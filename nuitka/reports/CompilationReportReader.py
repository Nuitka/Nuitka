#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" This is for use in testing, but also for user tools too."""

from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.TreeXML import fromFile
from nuitka.utils.ModuleNames import ModuleName


def parseCompilationReport(filename):
    return fromFile(filename)


def extractModulesUsedByModule(compilation_report, module_name):
    # Note: Avoiding usage of "xpath", to lower requirements to not need lxml.
    for module_node in compilation_report.findall("module"):
        if module_node.attrib["name"] != module_name:
            continue

        result = OrderedDict()

        for module_usage_node in module_node.find("module_usages").findall(
            "module_usage"
        ):
            entry = OrderedDict(module_usage_node.attrib)

            used_module_name = ModuleName(entry["name"])
            del entry["name"]
            entry["line"] = int(entry["line"])
            entry["excluded"] = bool(entry["finding"] == "excluded")

            result[used_module_name] = entry

        return result

    # Not found, no usages, user needs to handle that.
    return None


def _getResolvedCompilationPath(path, prefixes):
    for prefix_name, prefix_path in prefixes:
        path = path.replace(prefix_name, prefix_path)

    return path


def getCompilationOutputBinary(compilation_report, prefixes):
    return _getResolvedCompilationPath(
        path=compilation_report.find("output").attrib["run_filename"], prefixes=prefixes
    )


def getCompilationOutputMode(compilation_report):
    return compilation_report.attrib["mode"]


def getEmbeddedDataFilenames(compilation_report):
    result = []

    for datafile_node in compilation_report.findall("data_file"):
        if "embed-run-time" in datafile_node.attrib["tags"].split(
            ","
        ) or "embed-compile-time" in datafile_node.attrib["tags"].split(","):
            result.append(datafile_node.attrib["name"])

    return result


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
