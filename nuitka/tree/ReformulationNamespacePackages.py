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
"""
Namespace packages of Python3.3 or higher

"""

import os

from nuitka import Options
from nuitka.nodes.AssignNodes import StatementAssignmentVariableName
from nuitka.nodes.AttributeNodes import makeExpressionAttributeLookup
from nuitka.nodes.CallNodes import ExpressionCallNoKeywords
from nuitka.nodes.ConstantRefNodes import makeConstantRefNode
from nuitka.nodes.ContainerMakingNodes import (
    makeExpressionMakeList,
    makeExpressionMakeTuple,
    makeExpressionMakeTupleOrConstant,
)
from nuitka.nodes.DictionaryNodes import StatementDictOperationSet
from nuitka.nodes.FutureSpecs import FutureSpec
from nuitka.nodes.ImportNodes import (
    ExpressionImportModuleNameHard,
    ExpressionImportName,
    makeExpressionImportModuleFixed,
)
from nuitka.nodes.ModuleAttributeNodes import (
    ExpressionModuleAttributeFileRef,
    ExpressionNuitkaLoaderCreation,
)
from nuitka.nodes.ModuleNodes import CompiledPythonPackage
from nuitka.nodes.SubscriptNodes import ExpressionSubscriptLookup
from nuitka.nodes.VariableRefNodes import ExpressionVariableNameRef
from nuitka.PythonVersions import python_version

from .TreeHelpers import makeStatementsSequenceFromStatement
from .VariableClosure import completeVariableClosures


def _makeCall(module_name, import_name, attribute_name, source_ref, *args):
    return ExpressionCallNoKeywords(
        called=makeExpressionAttributeLookup(
            expression=ExpressionImportModuleNameHard(
                module_name=module_name, import_name=import_name, source_ref=source_ref
            ),
            attribute_name=attribute_name,
            source_ref=source_ref,
        ),
        args=makeExpressionMakeTupleOrConstant(
            elements=args, user_provided=True, source_ref=source_ref
        ),
        source_ref=source_ref,
    )


def getNameSpacePathExpression(package, source_ref):
    """Create the __path__ expression for a package."""

    reference_mode = Options.getFileReferenceMode()

    if reference_mode == "original":
        return makeConstantRefNode(
            constant=[package.getCompileTimeDirectory()],
            source_ref=source_ref,
        )
    elif reference_mode == "frozen":
        return makeConstantRefNode(
            constant=[],
            source_ref=source_ref,
        )
    else:
        elements = [
            ExpressionCallNoKeywords(
                called=makeExpressionAttributeLookup(
                    expression=ExpressionImportModuleNameHard(
                        module_name="os", import_name="path", source_ref=source_ref
                    ),
                    attribute_name="dirname",
                    source_ref=source_ref,
                ),
                args=makeExpressionMakeTuple(
                    elements=(
                        ExpressionModuleAttributeFileRef(
                            variable=package.getVariableForReference("__file__"),
                            source_ref=source_ref,
                        ),
                    ),
                    source_ref=source_ref,
                ),
                source_ref=source_ref,
            )
        ]

        if package.canHaveExternalImports():
            parts = package.getFullName().asString().split(".")

            for count in range(len(parts)):
                path_part = _makeCall(
                    "os",
                    "environ",
                    "get",
                    source_ref,
                    makeConstantRefNode(
                        constant="NUITKA_PACKAGE_%s" % "_".join(parts[: count + 1]),
                        source_ref=source_ref,
                    ),
                    makeConstantRefNode(constant="/notexist", source_ref=source_ref),
                )

                if parts[count + 1 :]:
                    path_part = _makeCall(
                        "os",
                        "path",
                        "join",
                        source_ref,
                        path_part,
                        makeConstantRefNode(
                            constant=os.path.join(*parts[count + 1 :]),
                            source_ref=source_ref,
                        ),
                    )

                elements.append(path_part)

        return makeExpressionMakeList(elements=elements, source_ref=source_ref)


def createPathAssignment(package, source_ref):
    return StatementAssignmentVariableName(
        provider=package,
        variable_name="__path__",
        source=getNameSpacePathExpression(package=package, source_ref=source_ref),
        source_ref=source_ref,
    )


def createPython3NamespacePath(package, source_ref):
    return StatementAssignmentVariableName(
        provider=package,
        variable_name="__path__",
        source=ExpressionCallNoKeywords(
            called=ExpressionImportName(
                module=makeExpressionImportModuleFixed(
                    module_name="_frozen_importlib"
                    if python_version < 0x350
                    else "_frozen_importlib_external",
                    source_ref=source_ref,
                ),
                import_name="_NamespacePath",
                level=0,
                source_ref=source_ref,
            ),
            args=makeExpressionMakeTupleOrConstant(
                elements=(
                    makeConstantRefNode(
                        constant=package.getFullName().asString(),
                        user_provided=True,
                        source_ref=source_ref,
                    ),
                    getNameSpacePathExpression(package=package, source_ref=source_ref),
                    makeConstantRefNode(constant=None, source_ref=source_ref),
                ),
                user_provided=True,
                source_ref=source_ref,
            ),
            source_ref=source_ref,
        ),
        source_ref=source_ref,
    )


def createNamespacePackage(module_name, is_top, source_ref):
    package = CompiledPythonPackage(
        module_name=module_name,
        is_top=is_top,
        mode="compiled",
        future_spec=FutureSpec(),
        source_ref=source_ref,
    )

    if python_version >= 0x300:
        statement = createPython3NamespacePath(package=package, source_ref=source_ref)
    else:
        statement = createPathAssignment(package, source_ref)

    package.setChild("body", makeStatementsSequenceFromStatement(statement=statement))

    completeVariableClosures(package)

    return package


def createImporterCacheAssignment(package, source_ref):
    return StatementDictOperationSet(
        dict_arg=ExpressionImportModuleNameHard(
            module_name="sys", import_name="path_importer_cache", source_ref=source_ref
        ),
        key=ExpressionSubscriptLookup(
            expression=ExpressionVariableNameRef(
                provider=package, variable_name="__path__", source_ref=source_ref
            ),
            subscript=makeConstantRefNode(constant=0, source_ref=source_ref),
            source_ref=source_ref,
        ),
        value=ExpressionNuitkaLoaderCreation(provider=package, source_ref=source_ref),
        source_ref=source_ref,
    )
