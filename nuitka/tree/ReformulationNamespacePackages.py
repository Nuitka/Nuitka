#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""
Namespace packages of Python3

"""

import os

from nuitka.nodes.AttributeNodes import makeExpressionAttributeLookup
from nuitka.nodes.CallNodes import ExpressionCallNoKeywords
from nuitka.nodes.ConstantRefNodes import makeConstantRefNode
from nuitka.nodes.ContainerMakingNodes import (
    makeExpressionMakeList,
    makeExpressionMakeTuple,
    makeExpressionMakeTupleOrConstant,
)
from nuitka.nodes.FutureSpecs import FutureSpec
from nuitka.nodes.ImportNodes import (
    ExpressionImportName,
    makeExpressionImportModuleFixed,
    makeExpressionImportModuleNameHard,
)
from nuitka.nodes.ModuleAttributeNodes import ExpressionModuleAttributeFileRef
from nuitka.nodes.ModuleNodes import CompiledPythonNamespacePackage
from nuitka.nodes.VariableNameNodes import StatementAssignmentVariableName
from nuitka.Options import getFileReferenceMode
from nuitka.PythonVersions import python_version

from .FutureSpecState import popFutureSpec, pushFutureSpec
from .TreeHelpers import (
    buildNode,
    makeStatementsSequenceFromStatement,
    parseSourceCodeToAst,
)
from .VariableClosure import completeVariableClosures


def _makeCall(module_name, import_name, attribute_name, source_ref, *args):
    return ExpressionCallNoKeywords(
        called=makeExpressionAttributeLookup(
            expression=makeExpressionImportModuleNameHard(
                module_name=module_name,
                import_name=import_name,
                module_guaranteed=True,
                source_ref=source_ref,
            ),
            attribute_name=attribute_name,
            source_ref=source_ref,
        ),
        args=makeExpressionMakeTupleOrConstant(
            elements=args, user_provided=True, source_ref=source_ref
        ),
        source_ref=source_ref,
    )


def _getNameSpacePathExpression(package, source_ref):
    """Create the __path__ expression for a package."""

    reference_mode = getFileReferenceMode()

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
        file_ref_node = ExpressionModuleAttributeFileRef(
            variable=package.getVariableForReference("__file__"),
            source_ref=source_ref,
        )

        if package.isCompiledPythonNamespacePackage():
            elements = [file_ref_node]
        else:
            elements = [
                ExpressionCallNoKeywords(
                    called=makeExpressionAttributeLookup(
                        expression=makeExpressionImportModuleNameHard(
                            module_name="os",
                            import_name="path",
                            module_guaranteed=True,
                            source_ref=source_ref,
                        ),
                        attribute_name="dirname",
                        source_ref=source_ref,
                    ),
                    args=makeExpressionMakeTuple(
                        elements=(file_ref_node,),
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
                    makeConstantRefNode(
                        constant=os.path.sep + "not_existing", source_ref=source_ref
                    ),
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

        return makeExpressionMakeList(elements=tuple(elements), source_ref=source_ref)


def createPathAssignment(package, source_ref):
    return StatementAssignmentVariableName(
        provider=package,
        variable_name="__path__",
        source=_getNameSpacePathExpression(package=package, source_ref=source_ref),
        source_ref=source_ref,
    )


def _getPathFinderFunction(package, source_ref):
    # TODO: This could be a shared helper function, but we currently cannot do these.
    ast_tree = parseSourceCodeToAst(
        source_code="_path_finder = lambda *args, **kw: None",
        module_name=package.getFullName(),
        filename=source_ref.getFilename(),
        line_offset=0,
    )

    pushFutureSpec(package.getFullName())
    statement = buildNode(package, ast_tree.body[0], source_ref)
    popFutureSpec()

    return statement.subnode_source


def createPython3NamespacePath(package, source_ref):

    module_name = (
        "_frozen_importlib" if python_version < 0x350 else "_frozen_importlib_external"
    )

    return StatementAssignmentVariableName(
        provider=package,
        variable_name="__path__",
        source=ExpressionCallNoKeywords(
            called=ExpressionImportName(
                module=makeExpressionImportModuleFixed(
                    using_module_name=package.getFullName(),
                    module_name=module_name,
                    value_name=module_name,
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
                    _getNameSpacePathExpression(package=package, source_ref=source_ref),
                    _getPathFinderFunction(package=package, source_ref=source_ref),
                ),
                user_provided=True,
                source_ref=source_ref,
            ),
            source_ref=source_ref,
        ),
        source_ref=source_ref,
    )


def createNamespacePackage(module_name, reason, is_top, source_ref):
    package = CompiledPythonNamespacePackage(
        module_name=module_name,
        reason=reason,
        is_top=is_top,
        mode="compiled",
        future_spec=FutureSpec(use_annotations=False),
        source_ref=source_ref,
    )

    if python_version >= 0x300:
        statement = createPython3NamespacePath(package=package, source_ref=source_ref)
    else:
        statement = createPathAssignment(package, source_ref)

    package.setChildBody(makeStatementsSequenceFromStatement(statement=statement))

    completeVariableClosures(package)

    return package


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
