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

from nuitka.tools.quality.auto_format.AutoFormat import (
    withFileOpenedAndAutoFormatted,
)
from nuitka.utils.Jinja2 import getTemplate

from .Common import writeLine

# specs
# -----
#  - StrNodes
#    operation_name, arg_name, shape, is_base, inheritance_base, base_name, simulator, simulator_return_value

specifications = [
    {
        "name": "StrNodes",
        "specs": [
            ["Join", "iterable", "Str", False, False, None, False, None],
            ["Partition", "sep", "Tuple", False, False, None, False, None],
            ["Rpartition", "sep", "Tuple", False, False, None, False, None],
            ["Strip2Base", "chars", "Str", True, False, None, True, None],
            ["Strip2", "chars", "Str", False, True, "Strip2", True, "str.strip"],
            ["Lstrip2", "chars", "Str", False, True, "Strip2", True, "str.lstrip"],
            ["Rstrip2", "chars", "Str", False, True, "Strip2", True, "str.rstrip"],
        ],
    }
]


def generate():
    for spec in specifications:
        template = getTemplate(
            package_name=__package__,
            template_subdir="templates_python",
            template_name="%s.py.j2" % spec["name"],
        )
        code = template.render(specifications=spec["specs"])
        with withFileOpenedAndAutoFormatted(
            os.path.join("nuitka/nodes", "%sGenerated.py" % spec["name"])
        ) as output_python:
            writeLine(output_python, code)
