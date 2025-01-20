#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" State of a stack of future specs during parsing. """

from nuitka.nodes.FutureSpecs import FutureSpec
from nuitka.plugins.Plugins import Plugins
from nuitka.PythonVersions import python_version

from .SyntaxErrors import raiseSyntaxError

_future_specs = []


def pushFutureSpec(module_name):
    _future_specs.append(
        FutureSpec(use_annotations=Plugins.decideAnnotations(module_name))
    )


def getFutureSpec():
    return _future_specs[-1]


def popFutureSpec():
    del _future_specs[-1]


def enableFutureFeature(node, object_name, source_ref):
    future_spec = _future_specs[-1]

    if object_name == "unicode_literals":
        future_spec.enableUnicodeLiterals()
    elif object_name == "absolute_import":
        future_spec.enableAbsoluteImport()
    elif object_name == "division":
        future_spec.enableFutureDivision()
    elif object_name == "print_function":
        future_spec.enableFuturePrint()
    elif object_name == "barry_as_FLUFL" and python_version >= 0x300:
        future_spec.enableBarry()
    elif object_name == "generator_stop":
        future_spec.enableGeneratorStop()
    elif object_name == "braces":
        raiseSyntaxError("not a chance", source_ref.atColumnNumber(node.col_offset))
    elif object_name in ("nested_scopes", "generators", "with_statement"):
        # These are enabled in all cases already.
        pass
    elif object_name == "annotations" and python_version >= 0x370:
        future_spec.enableFutureAnnotations()
    else:
        raiseSyntaxError(
            "future feature %s is not defined" % object_name,
            source_ref.atColumnNumber(node.col_offset),
        )


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
