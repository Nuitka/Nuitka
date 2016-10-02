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
""" Reformulation of import statements.

Consult the developer manual for information. TODO: Add ability to sync
source code comments with developer manual sections.

"""

from nuitka import Options
from nuitka.nodes.AssignNodes import (
    ExpressionTargetTempVariableRef,
    ExpressionTargetVariableRef,
    StatementAssignmentVariable,
    StatementReleaseVariable
)
from nuitka.nodes.ImportNodes import (
    ExpressionImportModule,
    ExpressionImportModuleHard,
    ExpressionImportName,
    StatementImportStar
)
from nuitka.nodes.NodeMakingHelpers import mergeStatements
from nuitka.nodes.StatementNodes import StatementsSequence
from nuitka.nodes.VariableRefNodes import ExpressionTempVariableRef
from nuitka.PythonVersions import python_version
from nuitka.tree import SyntaxErrors

from .Helpers import mangleName
from .ReformulationTryFinallyStatements import makeTryFinallyStatement

# For checking afterwards, if __future__ imports really were at the beginning
# of the file.
_future_import_nodes = []

def checkFutureImportsOnlyAtStart(body):
    # Check if a __future__ imports really were at the beginning of the file.
    for node in body:
        if node in _future_import_nodes:
            _future_import_nodes.remove(node)
        else:
            if _future_import_nodes:
                SyntaxErrors.raiseSyntaxError(
                    reason     = """\
from __future__ imports must occur at the beginning of the file""",
                    col_offset = 1
                      if python_version >= 300 or \
                      not Options.isFullCompat() else
                    None,
                    source_ref = _future_import_nodes[0].source_ref
                )

def _handleFutureImport(provider, node, source_ref):
    # Don't allow future imports in functions or classes.
    if not provider.isCompiledPythonModule():
        SyntaxErrors.raiseSyntaxError(
            reason     = """\
from __future__ imports must occur at the beginning of the file""",
            col_offset = 8
              if python_version >= 300 or \
              not Options.isFullCompat()
            else None,
            source_ref = source_ref
        )


    for import_desc in node.names:
        object_name, _local_name = import_desc.name, import_desc.asname

        _enableFutureFeature(
            object_name = object_name,
            future_spec = source_ref.getFutureSpec(),
            source_ref  = source_ref
        )

    # Remember it for checks to be applied once module is complete, e.g. if
    # they are all at module start.
    node.source_ref = source_ref
    _future_import_nodes.append(node)


def _enableFutureFeature(object_name, future_spec, source_ref):
    if object_name == "unicode_literals":
        future_spec.enableUnicodeLiterals()
    elif object_name == "absolute_import":
        future_spec.enableAbsoluteImport()
    elif object_name == "division":
        future_spec.enableFutureDivision()
    elif object_name == "print_function":
        future_spec.enableFuturePrint()
    elif object_name == "barry_as_FLUFL" and python_version >= 300:
        future_spec.enableBarry()
    elif object_name == "generator_stop":
        future_spec.enableGeneratorStop()
    elif object_name == "braces":
        SyntaxErrors.raiseSyntaxError(
            "not a chance",
            source_ref
        )
    elif object_name in ("nested_scopes", "generators", "with_statement"):
        # These are enabled in all cases already.
        pass
    else:
        SyntaxErrors.raiseSyntaxError(
            "future feature %s is not defined" % object_name,
            source_ref
        )


def buildImportFromNode(provider, node, source_ref):
    # "from .. import .." statements. This may trigger a star import, or
    # multiple names being looked up from the given module variable name.
    # This is pretty complex, pylint: disable=R0912,R0914

    module_name = node.module if node.module is not None else ""
    level = node.level

    # Importing from "__future__" module may enable flags to the parser,
    # that we need to know about, handle that.
    if module_name == "__future__":
        _handleFutureImport(provider, node, source_ref)

    target_names = []
    import_names = []

    # Mapping imported "fromlist" to assigned "fromlist" if any, handling the
    # star case as well.
    for import_desc in node.names:
        object_name, local_name = import_desc.name, import_desc.asname

        if object_name == '*':
            target_names.append(None)
            assert local_name is None
        else:
            target_names.append(
                local_name
                  if local_name is not None else
                object_name
            )

        import_names.append(object_name)

    # Star imports get special treatment.
    if None in target_names:
        # More than "*" is a syntax error in Python, need not care about this at
        # all, it's only allowed value for import list in  this case.
        assert target_names == [None]

        # Python3 made it so that these can only occur on the module level,
        # so this a syntax error if not there. For Python2 it is OK to
        # occur everywhere though.
        if not provider.isCompiledPythonModule() and python_version >= 300:
            SyntaxErrors.raiseSyntaxError(
                "import * only allowed at module level",
                provider.getSourceReference()
            )

        # Functions with star imports get a marker.
        if provider.isExpressionFunctionBody():
            provider.markAsStarImportContaining()

        return StatementImportStar(
            module_import = ExpressionImportModule(
                module_name = module_name,
                import_list = ('*',),
                level       = level,
                source_ref  = source_ref
            ),
            source_ref    = source_ref
        )
    else:
        def makeImportName(import_name):
            if module_name == "__future__":
                # Make "__future__" imports tie hard immediately, they cannot be
                # any other way.
                return ExpressionImportModuleHard(
                    module_name = "__future__",
                    import_name = import_name,
                    source_ref  = source_ref
                )
            else:
                # Refer to be module, or a clone of the reference if need be.
                return ExpressionImportName(
                    module      = imported_from_module,
                    import_name = import_name,
                    source_ref  = source_ref
                )

        imported_from_module = ExpressionImportModule(
            module_name = module_name,
            import_list = tuple(import_names),
            level       = level,
            source_ref  = source_ref
        )

        # If we have multiple names to import, consider each.
        multi_names = len(target_names) > 1

        statements = []

        if multi_names:
            tmp_import_from = provider.allocateTempVariable(
                temp_scope = provider.allocateTempScope("import_from"),
                name       = "module"
            )

            statements.append(
                StatementAssignmentVariable(
                    variable_ref = ExpressionTargetTempVariableRef(
                        variable   = tmp_import_from,
                        source_ref = source_ref
                    ),
                    source       = imported_from_module,
                    source_ref   = source_ref
                )
            )

            imported_from_module = ExpressionTempVariableRef(
                variable   = tmp_import_from,
                source_ref = source_ref
            )

        import_statements = []
        first = True

        for target_name, import_name in zip(target_names, import_names):
            # Make a clone of the variable reference, if we are going to use
            # another one.
            if not first:
                imported_from_module = imported_from_module.makeClone()
            first = False

            import_statements.append(
                StatementAssignmentVariable(
                    variable_ref = ExpressionTargetVariableRef(
                        variable_name = mangleName(target_name, provider),
                        source_ref    = source_ref
                    ),
                    source       = makeImportName(
                        import_name = import_name,
                    ),
                    source_ref   = source_ref
                )
            )

        # Release the temporary module value as well.
        if multi_names:
            statements.append(
                makeTryFinallyStatement(
                    provider   = provider,
                    tried      = import_statements,
                    final      = (
                        StatementReleaseVariable(
                            variable   = tmp_import_from,
                            source_ref = source_ref
                        ),
                    ),
                    source_ref = source_ref
                )
            )
        else:
            statements.extend(import_statements)

        # Note: Each import is sequential. It can succeed, and the failure of a
        # later one is not undoing previous ones. We can therefore have a
        # sequence of imports that each only import one thing therefore.
        return StatementsSequence(
            statements = mergeStatements(statements),
            source_ref = source_ref
        )
