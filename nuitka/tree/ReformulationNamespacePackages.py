#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
Namespace packages of Python3.3

"""

from nuitka.nodes.ModuleNodes import PythonPackage

from nuitka.SourceCodeReferences import SourceCodeReference
from nuitka.nodes.FutureSpecs import FutureSpec

from nuitka.tree.Helpers import makeStatementsSequenceFromStatement
from nuitka.nodes.AssignNodes import StatementAssignmentVariable
from nuitka.nodes.VariableRefNodes import ExpressionTargetVariableRef
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.tree.VariableClosure import completeVariableClosures
from nuitka.nodes.CallNodes import ExpressionCallNoKeywords
from nuitka.nodes.ImportNodes import (
    ExpressionImportName,
    ExpressionImportModule
)

def createNamespacePackage(package_name, module_relpath):
    parts = package_name.split(".")

    source_ref = SourceCodeReference.fromFilenameAndLine(
        module_relpath,
        1,
        FutureSpec(),
        False
    )
    source_ref = source_ref.atInternal()

    package_package_name = ".".join(parts[:-1]) or None
    package = PythonPackage(
        name         = parts[-1],
        package_name = package_package_name,
        source_ref   = source_ref,
    )

    package.setBody(
        makeStatementsSequenceFromStatement(
            statement = (
                StatementAssignmentVariable(
                    variable_ref = ExpressionTargetVariableRef(
                        variable_name = "__path__",
                        source_ref    = source_ref
                    ),
                    source       = ExpressionCallNoKeywords(
                        called = ExpressionImportName(
                            module = ExpressionImportModule(
                                module_name    = "_frozen_importlib",
                                import_list    = (),
                                level          = 0,
                                source_ref     = source_ref
                            ),
                            import_name = "_NamespacePath",
                            source_ref  = source_ref
                        ),
                        args = ExpressionConstantRef(
                            constant   = (
                                package_name,
                                [ module_relpath ],
                                None
                            ),
                            source_ref =  source_ref
                        ),
                        source_ref =  source_ref
                    ),
                    source_ref = source_ref
                )
            )
        )
    )

    completeVariableClosures( package )

    return source_ref, package
