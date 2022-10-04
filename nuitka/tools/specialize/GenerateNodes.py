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
import os

from jinja2 import Template

# specs
# -----
#  operation_name, arg_name, shape, is_base

specifications = [
    {
        "name": "StrNodes",
        "specs": [
            ["Join", "iterable", "Str", False],
            ["Partition", "sep", "Tuple", False],
            ["Rpartition", "sep", "Tuple", False],
            ["Strip2Base", "chars", "Str", True],
        ],
    }
]


def main():
    for spec in specifications:
        with open(
            os.path.join(
                "nuitka/tools/specialize/templates_python", "%s.py.j2" % spec["name"]
            )
        ) as template_file:
            template = Template(template_file.read())

        with open(
            os.path.join("nuitka/nodes", "%sGenerated.py" % spec["name"]),
            "w",
            encoding="utf-8",
        ) as output_python:
            code = template.render(specifications=spec["specs"])
            output_python.write(code)


main()
