#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
from nuitka.nodes.AttributeNodes import ExpressionAttributeLookup
from nuitka.nodes.CallNodes import ExpressionCallNoKeywords
from nuitka.nodes.ConstantRefNodes import makeConstantRefNode
from nuitka.nodes.ContainerMakingNodes import ExpressionMakeList, ExpressionMakeTuple
from nuitka.nodes.FutureSpecs import FutureSpec
from nuitka.nodes.ImportNodes import (
    ExpressionImportModuleNameHard,
    ExpressionImportName,
)
from nuitka.nodes.ModuleAttributeNodes import ExpressionModuleAttributeFileRef
from nuitka.nodes.ModuleNodes import CompiledPythonPackage
from nuitka.PythonVersions import python_version
from nuitka.SourceCodeReferences import SourceCodeReference

from .TreeHelpers import makeAbsoluteImportNode, makeStatementsSequenceFromStatement
from .VariableClosure import completeVariableClosures


def _makeCall(module_name, import_name, attribute_name, source_ref, *args):
    return ExpressionCallNoKeywords(
        called=ExpressionAttributeLookup(
            source=ExpressionImportModuleNameHard(
                module_name=module_name, import_name=import_name, source_ref=source_ref
            ),
            attribute_name=attribute_name,
            source_ref=source_ref,
        ),
        args=ExpressionMakeTuple(elements=args, source_ref=source_ref),
        source_ref=source_ref,
    )


def createPathAssignment(package, source_ref):
    if Options.getFileReferenceMode() == "original":
        path_value = makeConstantRefNode(
            constant=[os.path.dirname(source_ref.getFilename())],
            source_ref=source_ref,
            user_provided=True,
        )
    else:
        elements = [
            ExpressionCallNoKeywords(
                called=ExpressionAttributeLookup(
                    source=ExpressionImportModuleNameHard(
                        module_name="os", import_name="path", source_ref=source_ref
                    ),
                    attribute_name="dirname",
                    source_ref=source_ref,
                ),
                args=ExpressionMakeTuple(
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
            parts = package.getFullName().split(".")

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

        path_value = ExpressionMakeList(elements=elements, source_ref=source_ref)

    return StatementAssignmentVariableName(
        provider=package,
        variable_name="__path__",
        source=path_value,
        source_ref=source_ref,
    )


def createPython3NamespacePath(package, module_relpath, source_ref):
    return StatementAssignmentVariableName(
        provider=package,
        variable_name="__path__",
        source=ExpressionCallNoKeywords(
            called=ExpressionImportName(
                module=makeAbsoluteImportNode(
                    module_name="_frozen_importlib"
                    if python_version < 350
                    else "_frozen_importlib_external",
                    source_ref=source_ref,
                ),
                import_name="_NamespacePath",
                level=None,
                source_ref=source_ref,
            ),
            args=makeConstantRefNode(
                constant=(package.getFullName(), [module_relpath], None),
                source_ref=source_ref,
            ),
            source_ref=source_ref,
        ),
        source_ref=source_ref,
    )


def createNamespacePackage(module_name, package_name, is_top, module_relpath):
    source_ref = SourceCodeReference.fromFilenameAndLine(
        filename=module_relpath, line=1
    )
    source_ref = source_ref.atInternal()

    package_name = package_name or None

    package = CompiledPythonPackage(
        name=module_name,
        package_name=package_name,
        is_top=is_top,
        mode="compiled",
        future_spec=FutureSpec(),
        source_ref=source_ref,
    )

    if python_version >= 300:
        statement = createPython3NamespacePath(
            package=package, module_relpath=module_relpath, source_ref=source_ref
        )
    else:
        statement = createPathAssignment(package, source_ref)

    package.setBody(makeStatementsSequenceFromStatement(statement=statement))

    completeVariableClosures(package)

    return source_ref, package
