#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka import Options
from nuitka.nodes.AssignNodes import (
    ExpressionTargetVariableRef,
    StatementAssignmentVariable
)
from nuitka.nodes.AttributeNodes import ExpressionAttributeLookup
from nuitka.nodes.CallNodes import ExpressionCallNoKeywords
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.ContainerMakingNodes import (
    ExpressionMakeList,
    ExpressionMakeTuple
)
from nuitka.nodes.FutureSpecs import FutureSpec
from nuitka.nodes.ImportNodes import (
    ExpressionImportModule,
    ExpressionImportModuleHard,
    ExpressionImportName
)
from nuitka.nodes.ModuleNodes import (
    CompiledPythonPackage,
    ExpressionModuleFileAttributeRef
)
from nuitka.PythonVersions import python_version
from nuitka.SourceCodeReferences import SourceCodeReference
from nuitka.utils.Utils import dirname

from .Helpers import makeStatementsSequenceFromStatement
from .VariableClosure import completeVariableClosures


def createPathAssignment(source_ref):
    if Options.getFileReferenceMode() == "original":
        path_value = ExpressionConstantRef(
            constant      = [
                dirname(source_ref.getFilename())
            ],
            source_ref    = source_ref,
            user_provided = True
        )
    else:
        path_value = ExpressionMakeList(
            elements   = (
                ExpressionCallNoKeywords(
                    called     = ExpressionAttributeLookup(
                        source         = ExpressionImportModuleHard(
                            module_name = "os",
                            import_name = "path",
                            source_ref  = source_ref
                        ),
                        attribute_name = "dirname",
                        source_ref     = source_ref
                    ),
                    args       = ExpressionMakeTuple(
                        elements   = (
                            ExpressionModuleFileAttributeRef(
                                source_ref = source_ref,
                            ),
                        ),
                        source_ref = source_ref,
                    ),
                    source_ref = source_ref,
                ),
            ),
            source_ref = source_ref
        )

    return  StatementAssignmentVariable(
        variable_ref = ExpressionTargetVariableRef(
            variable_name = "__path__",
            source_ref    = source_ref
        ),
        source       = path_value,
        source_ref   = source_ref
    )


def createPython3NamespacePath(package_name, module_relpath, source_ref):
    return StatementAssignmentVariable(
        variable_ref = ExpressionTargetVariableRef(
            variable_name = "__path__",
            source_ref    = source_ref
        ),
        source       = ExpressionCallNoKeywords(
            called     = ExpressionImportName(
                module      = ExpressionImportModule(
                    module_name = "_frozen_importlib"
                                    if python_version < 350 else
                                  "_frozen_importlib_external",
                    import_list = (),
                    level       = 0,
                    source_ref  = source_ref
                ),
                import_name = "_NamespacePath",
                source_ref  = source_ref
            ),
            args       = ExpressionConstantRef(
                constant   = (
                    package_name,
                    [module_relpath],
                    None
                ),
                source_ref =  source_ref
            ),
            source_ref =  source_ref
        ),
        source_ref   = source_ref
    )


def createNamespacePackage(package_name, module_relpath):
    parts = package_name.split('.')

    source_ref = SourceCodeReference.fromFilenameAndLine(
        filename    = module_relpath,
        line        = 1,
        future_spec = FutureSpec(),
    )
    source_ref = source_ref.atInternal()

    package_package_name = '.'.join(parts[:-1]) or None
    package = CompiledPythonPackage(
        name         = parts[-1],
        mode         = "compiled",
        package_name = package_package_name,
        source_ref   = source_ref,
    )

    if python_version >= 300:
        statement = createPython3NamespacePath(
            package_name   = package_name,
            module_relpath = module_relpath,
            source_ref     = source_ref
        )
    else:
        statement = createPathAssignment(source_ref)

    package.setBody(
        makeStatementsSequenceFromStatement(
            statement = statement
        )
    )

    completeVariableClosures(package)

    return source_ref, package
