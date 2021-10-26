#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" This tool is generating node variants from Jinja templates.

"""

import nuitka.Options

nuitka.Options.is_fullcompat = False

# isort:start

import nuitka.codegen.ComparisonCodes
import nuitka.codegen.HelperDefinitions
import nuitka.codegen.Namify
from nuitka.utils.Jinja2 import getTemplate

from .Common import withFileOpenedAndAutoformatted, writeline

# This defines which attribute nodes are to specialize and how
# to do that.
attribute_information = {
    "items": ("tshape_dict",),
    "iteritems": ("tshape_dict",),
}

attribute_shape_versions = {("iteritems", "tshape_dict"): "str is bytes"}


def emitGenerationWarning(emit, template_name):
    emit(
        '''"""Specialized attribute nodes

WARNING, this code is GENERATED. Modify the template %s instead!"""'''
        % template_name
    )


def makeAttributeNodes():
    filename_python = "nuitka/nodes/AttributeNodesGenerated.py"

    template = getTemplate(
        package_name=__package__,
        template_subdir="templates_python",
        template_name="AttributeNodeFixed.py.j2",
    )

    with withFileOpenedAndAutoformatted(filename_python) as output_python:

        def emit(*args):
            writeline(output_python, *args)

        emitGenerationWarning(emit, template.name)

        emit("from .AttributeLookupNodes import ExpressionAttributeLookupFixedBase")
        emit("from nuitka.specs.BuiltinParameterSpecs import extractBuiltinArgs")

        emit("attribute_classes = {}")

        for attribute_name, shape_names in sorted(attribute_information.items()):
            # Some attributes lead to different operations for Python3.
            if attribute_name == "items":
                python3_operation_name = "iteritems"
            else:
                python3_operation_name = None

            code = template.render(
                attribute_name=attribute_name,
                python3_operation_name=python3_operation_name,
                shape_names=shape_names,
                attribute_shape_versions=attribute_shape_versions,
                name=template.name,
            )

            emit(code)


def main():
    makeAttributeNodes()
