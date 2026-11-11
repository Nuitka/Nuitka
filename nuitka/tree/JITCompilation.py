#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Helpers for JIT related function building and compilation decisions."""

import ast
import symtable

from nuitka.nodes.BuiltinDictNodes import ExpressionBuiltinDict
from nuitka.nodes.ConstantRefNodes import makeConstantRefNode
from nuitka.nodes.DictionaryNodes import StatementDictOperationSet
from nuitka.nodes.ExecEvalNodes import ExpressionBuiltinExec
from nuitka.nodes.GlobalsLocalsNodes import ExpressionBuiltinGlobals
from nuitka.nodes.KeyValuePairNodes import (
    makeExpressionKeyValuePairConstantKey,
)
from nuitka.nodes.NodeMakingHelpers import (
    makeExpressionBuiltinLocals,
    makeVariableRefNode,
)
from nuitka.nodes.StatementNodes import StatementExpressionOnly
from nuitka.nodes.SubscriptNodes import makeExpressionIndexLookup
from nuitka.nodes.VariableNameNodes import (
    ExpressionVariableNameRef,
    StatementAssignmentVariableName,
)
from nuitka.plugins.Hooks import getJITDecoratorRegistrations
from nuitka.Tracing import general

from .AstUnparsing import unparseNode
from .ReformulationExecStatements import wrapEvalGlobalsAndLocals
from .ReformulationTryFinallyStatements import makeTryFinallyStatement
from .TreeHelpers import makeStatementsSequence

_provider_import_aliases = {}
_module_source_lines = None
_module_symbol_table = None


def clearDecoratorImportAliasesCache():
    """Reset the module tree caches after a module tree is built."""
    # Singleton caches, pylint: disable=global-statement
    global _module_source_lines, _module_symbol_table

    _provider_import_aliases.clear()
    _module_source_lines = None
    _module_symbol_table = None


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


def _getNodeLineRange(node):
    start_line = node.lineno

    if node.decorator_list:
        start_line = min(
            [start_line] + [decorator.lineno for decorator in node.decorator_list]
        )

    end_line = getattr(node, "end_lineno", None)

    if end_line is None:
        end_line = max(
            getattr(child_node, "lineno", start_line) for child_node in ast.walk(node)
        )

    return start_line, end_line


def _getModuleSourceLines(module):
    global _module_source_lines  # singleton, pylint: disable=global-statement

    if _module_source_lines is None:
        _module_source_lines = tuple(module.getSourceCode().splitlines(True))

    return _module_source_lines


def _getModuleSymbolTable(module):
    global _module_symbol_table  # singleton, pylint: disable=global-statement

    if _module_symbol_table is None:
        source_code = module.getSourceCode()

        # Only called for functions of modules that are built from source.
        assert source_code is not None, module

        _module_symbol_table = symtable.symtable(
            source_code, module.getCompileTimeFilename(), "exec"
        )

    return _module_symbol_table


def _findFunctionSymbolTable(table, function_name, line_number):
    line_match = None

    for child in table.get_children():
        if child.get_type() == "function" and child.get_lineno() == line_number:
            if child.get_name() == function_name:
                return child

            # The name can be mangled for private names of classes, in which
            # case the line number is still unique.
            if line_match is None:
                line_match = child

        result = _findFunctionSymbolTable(child, function_name, line_number)

        if result is not None:
            return result

    return line_match


def _getFunctionFreeVariableNames(module, node):
    """Get the free variable names of a function, i.e. its closure variables.

    Notes:
        This uses the module symbol table, so that functions that reference
        names from an enclosing function are known before their body is
        parsed, which the JIT compilation mode avoids.

    Args:
        module: The module the function is contained in.
        node: The AST node of the function.

    Returns:
        Tuple of free variable names, sorted.
    """

    function_table = _findFunctionSymbolTable(
        table=_getModuleSymbolTable(module),
        function_name=node.name,
        line_number=node.lineno,
    )

    assert function_table is not None, node.name

    return tuple(
        sorted(
            symbol.get_name()
            for symbol in function_table.get_symbols()
            if symbol.is_free()
        )
    )


def _getDecoratorRegistrations(provider, decorator):
    decorator_registrations = getJITDecoratorRegistrations()

    for full_name in _getDecoratorFullNames(provider, decorator):
        for registration in decorator_registrations.get(full_name, ()):
            yield (full_name,) + registration


def decideFunctionCompilationMode(provider, node, decorators):
    """Decide how to compile a function based on decorator names.

    Returns:
        tuple of compilation mode and logger to use for related errors.
    """
    compilation_mode = "compiled"
    compilation_logger = general
    module = provider.getParentModule()
    start_line, end_line = _getNodeLineRange(node)
    get_lines = None

    for decorator in decorators:
        decorator_name = _getDecoratorSyntacticName(decorator)

        # Hard coded name.
        if decorator_name == "nuitka_ignore":
            compilation_mode = "bytecode"
            compilation_logger = general
            continue

        for registered_name, mode, callback, plugin in _getDecoratorRegistrations(
            provider, decorator
        ):
            if mode == "bytecode":
                compilation_mode = "bytecode"
                compilation_logger = plugin
            else:
                if get_lines is None:

                    def get_lines():
                        return _getModuleSourceLines(module)

                callback(
                    decorator_name=registered_name,
                    module=module,
                    start_line=start_line,
                    end_line=end_line,
                    get_lines=get_lines,
                    node=node,
                )

    return compilation_mode, compilation_logger


def buildBytecodeOrSourceFunction(provider, node, compilation_mode, source_ref, logger):
    # TODO: We should have a compile() builtin usage here, lookup "co_code" and
    # support that as a constant value. We then would have the "bytecode" only
    # in the binary, right now "bytecode" and "source" make no difference.
    #  pylint: disable=unused-argument
    source_line = node.lineno

    if node.decorator_list:
        source_line = min(
            [source_line] + [decorator.lineno for decorator in node.decorator_list]
        )

    # Preserve line numbers, so that source inspection of the bytecode
    # function finds the right lines in the module source.
    source_code = "\n" * (source_line - 1) + unparseNode(node, logger=logger)

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

    # Functions with closure variables are executed with a namespace that
    # contains them as globals. The "exec" creates a module level function,
    # which can only access these through its globals, but the JIT will then
    # find the values it needs. The actual locals are still used, so that
    # decorators and default values can see them too.
    free_variable_names = _getFunctionFreeVariableNames(
        module=provider.getParentModule(), node=node
    )

    source_variable, globals_ref, locals_ref, tried, final = wrapEvalGlobalsAndLocals(
        provider=provider,
        locals_scope=provider.getLocalsScope(),
        source_node=source,
        globals_node=(
            ExpressionBuiltinDict(
                pos_arg=ExpressionBuiltinGlobals(source_ref=source_ref),
                pairs=tuple(
                    makeExpressionKeyValuePairConstantKey(
                        key=variable_name,
                        value=ExpressionVariableNameRef(
                            provider=provider,
                            variable_name=variable_name,
                            source_ref=source_ref,
                        ),
                    )
                    for variable_name in free_variable_names
                    if variable_name != node.name
                ),
                source_ref=source_ref,
            )
            if free_variable_names
            else None
        ),
        locals_node=(
            makeExpressionBuiltinLocals(
                locals_scope=provider.getLocalsScope(), source_ref=source_ref
            )
            if free_variable_names
            else None
        ),
        temp_scope=provider.allocateTempScope("function_exec"),
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

    if node.name in free_variable_names:
        # Make the function itself available in its namespace, so that
        # recursive calls resolve.
        exec_statements.append(
            StatementDictOperationSet(
                dict_arg=makeVariableRefNode(
                    variable=globals_ref.getVariable(), source_ref=source_ref
                ),
                key=makeConstantRefNode(constant=node.name, source_ref=source_ref),
                value=makeExpressionIndexLookup(
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
