#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Helpers for JIT related function building and compilation decisions."""

import ast

from nuitka.nodes.ConstantRefNodes import makeConstantRefNode
from nuitka.nodes.ExecEvalNodes import ExpressionBuiltinExec
from nuitka.nodes.NodeMakingHelpers import makeVariableRefNode
from nuitka.nodes.StatementNodes import StatementExpressionOnly
from nuitka.nodes.SubscriptNodes import makeExpressionIndexLookup
from nuitka.nodes.VariableNameNodes import StatementAssignmentVariableName
from nuitka.plugins.Hooks import getUncompiledDecoratorNames

from .ReformulationExecStatements import wrapEvalGlobalsAndLocals
from .ReformulationTryFinallyStatements import makeTryFinallyStatement
from .TreeHelpers import makeStatementsSequence

_provider_import_aliases = {}


def clearDecoratorImportAliasesCache():
    """Reset the import alias cache after a module tree is built."""
    _provider_import_aliases.clear()


def _getProviderImportAliases(provider):
    result = _provider_import_aliases.get(provider)

    if result is None:
        result = {}, set()
        _provider_import_aliases[provider] = result

    return result


def _addDecoratorImportAlias(aliases, alias_name, target_name):
    if alias_name in aliases:
        if aliases[alias_name] != target_name:
            # The same name is imported from different places, so it cannot
            # be resolved safely.
            aliases[alias_name] = None
    else:
        aliases[alias_name] = target_name


def recordImportModule(provider, module_name, local_name):
    """Record an "import" statement for later decorator name resolution."""
    aliases, _star_modules = _getProviderImportAliases(provider)

    if local_name is not None:
        _addDecoratorImportAlias(aliases, local_name, module_name)
    else:
        root_name = module_name.split(".")[0]
        _addDecoratorImportAlias(aliases, root_name, root_name)


def recordImportFrom(provider, module_name, import_names, target_names):
    """Record a "from ... import ..." statement for decorator name resolution."""
    aliases, star_modules = _getProviderImportAliases(provider)

    for import_name, target_name in zip(import_names, target_names):
        if import_name == "*":
            star_modules.add(module_name)
        else:
            _addDecoratorImportAlias(
                aliases, target_name, module_name + "." + import_name
            )


def _getDecoratorImportAliases(provider):
    aliases = {}
    star_modules = set()

    current = provider

    while current is not None:
        current_aliases, current_star_modules = _provider_import_aliases.get(
            current, ({}, ())
        )

        for alias_name, target_name in current_aliases.items():
            if alias_name not in aliases:
                aliases[alias_name] = target_name

        star_modules.update(current_star_modules)

        current = current.getParentVariableProvider()

    return aliases, star_modules


def _getDecoratorSyntacticName(decorator):
    if decorator.isExpressionCall():
        return _getDecoratorSyntacticName(decorator.subnode_called)

    if decorator.isExpressionVariableNameRef():
        return decorator.getVariableName()

    if decorator.isExpressionAttributeLookup():
        root_name = _getDecoratorSyntacticName(decorator.subnode_expression)

        if root_name is None:
            return None

        return root_name + "." + decorator.getAttributeName()

    return None


def _getDecoratorFullNames(provider, decorator):
    decorator_name = _getDecoratorSyntacticName(decorator)

    if decorator_name is None:
        return ()

    aliases, star_modules = _getDecoratorImportAliases(provider)

    if "." in decorator_name:
        root_name, attribute_path = decorator_name.split(".", 1)

        if root_name not in aliases:
            result = (decorator_name,)
        elif aliases[root_name] is None:
            result = ()
        else:
            result = (aliases[root_name] + "." + attribute_path,)
    elif decorator_name not in aliases:
        result = tuple(
            star_module + "." + decorator_name for star_module in star_modules
        )
    elif aliases[decorator_name] is None:
        result = ()
    else:
        result = (aliases[decorator_name],)

    return result


def _isUncompiledDecorator(provider, decorator):
    decorator_name = _getDecoratorSyntacticName(decorator)

    # Hard coded name.
    if decorator_name == "nuitka_ignore":
        return True

    decorator_names = getUncompiledDecoratorNames()

    for full_name in _getDecoratorFullNames(provider, decorator):
        if full_name in decorator_names:
            return True

    return False


def decideFunctionCompilationMode(provider, decorators):
    """Decide how to compile a function based on decorator names."""
    for decorator in decorators:
        if _isUncompiledDecorator(provider, decorator):
            return "bytecode"

    return "compiled"


def buildBytecodeOrSourceFunction(provider, node, compilation_mode, source_ref):
    # TODO: We should have a compile() builtin usage here, lookup "co_code" and
    # support that as a constant value. We then would have the "bytecode" only
    # in the binary, right now "bytecode" and "source" make no difference.
    #  pylint: disable=unused-argument
    source_code = ast.unparse(node)

    source = makeConstantRefNode(
        constant=source_code,
        source_ref=source_ref,
        user_provided=True,
    )

    # if compilation_mode == "bytecode":
    #     source = ExpressionBuiltinCompile(
    #         source_code=source,
    #         filename=makeConstantRefNode(constant="<exec>", source_ref=source_ref),
    #         mode=makeConstantRefNode(constant="exec", source_ref=source_ref),
    #         flags=None,
    #         dont_inherit=None,
    #         optimize=None,
    #         source_ref=source_ref
    #     )

    # This is actually for the globals locals usage to be default values of the
    # scope.

    temp_scope = provider.allocateTempScope("function_exec")

    source_variable, globals_ref, locals_ref, tried, final = wrapEvalGlobalsAndLocals(
        provider=provider,
        locals_scope=provider.getLocalsScope(),
        source_node=source,
        globals_node=None,
        locals_node=None,
        temp_scope=temp_scope,
        source_ref=source_ref,
    )

    exec_statements = [
        StatementExpressionOnly(
            expression=ExpressionBuiltinExec(
                source_code=makeVariableRefNode(
                    variable=source_variable, source_ref=source_ref
                ),
                globals_arg=globals_ref,
                locals_arg=locals_ref,
                closure=None,
                source_ref=source_ref,
            ),
            source_ref=source_ref,
        )
    ]

    if provider.isExpressionFunctionBody():
        # The "exec" updates the locals dictionary, but not the optimized
        # local variable of the function body. Assign the defined name back,
        # so that nested uncompiled functions and classes remain visible.
        exec_statements.append(
            StatementAssignmentVariableName(
                provider=provider,
                variable_name=node.name,
                source=makeExpressionIndexLookup(
                    expression=makeVariableRefNode(
                        variable=locals_ref.getVariable(), source_ref=source_ref
                    ),
                    index_value=node.name,
                    source_ref=source_ref,
                ),
                source_ref=source_ref,
            )
        )

    tried = makeStatementsSequence(
        statements=(tried, tuple(exec_statements)),
        source_ref=source_ref,
    )

    # Hack: Allow some APIs to work already
    # tried.parent = provider

    return makeTryFinallyStatement(
        provider=provider,
        tried=tried,
        final=final,
        source_ref=source_ref,
    )


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
