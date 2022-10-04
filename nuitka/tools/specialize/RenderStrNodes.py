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
from jinja2 import Template

specifications = [
    ["Join", "iterable", "Str", False],
    ["Partition", "sep", "Tuple", False],
    ["Rpartition", "sep", "Tuple", False],
    ["Strip2Base", "chars", "Str", True],
]


def main():
    with open(
        "nuitka/tools/specialize/templates_python/StrNodes.py.j2"
    ) as template_file:
        template = Template(template_file.read())

    with open("StrNodes.py", "w", encoding="utf-8") as output_python:
        code = template.render(specifications=specifications)
        output_python.write(code)


main()
