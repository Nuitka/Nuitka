#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Code to generate and interact with compiled function objects.

"""

from nuitka.PythonVersions import python_version

from .CodeHelpers import generateStatementSequenceCode
from .CodeObjectCodes import getCodeObjectAccessCode
from .Emission import SourceCodeCollector
from .FunctionCodes import (
    finalizeFunctionLocalVariables,
    getClosureCopyCode,
    getFunctionCreationArgs,
    getFunctionQualnameObj,
    setupFunctionLocalVariables,
)
from .Indentation import indented
from .ModuleCodes import getModuleAccessCode
from .templates.CodeTemplatesGeneratorFunction import (
    template_generator_context_body_template,
    template_generator_context_maker_decl,
    template_generator_exception_exit,
    template_generator_noexception_exit,
    template_generator_return_exit,
    template_make_empty_generator,
    template_make_generator,
)
from .YieldCodes import getYieldReturnDispatchCode


def _getGeneratorMakerIdentifier(function_identifier):
    return "MAKE_GENERATOR_" + function_identifier


def getGeneratorObjectDeclCode(function_identifier, closure_variables):
    generator_creation_args = getFunctionCreationArgs(
        defaults_name=None,
        kw_defaults_name=None,
        annotations_name=None,
        closure_variables=closure_variables,
    )

    return template_generator_context_maker_decl % {
        "generator_maker_identifier": _getGeneratorMakerIdentifier(function_identifier),
        "generator_creation_args": ", ".join(generator_creation_args),
    }


def getGeneratorObjectCode(
    context,
    function_identifier,
    closure_variables,
    user_variables,
    outline_variables,
    temp_variables,
    needs_exception_exit,
    needs_generator_return,
):
    # A bit of details going on here, pylint: disable=too-many-locals

    setupFunctionLocalVariables(
        context=context,
        parameters=None,
        closure_variables=closure_variables,
        user_variables=user_variables + outline_variables,
        temp_variables=temp_variables,
    )

    function_codes = SourceCodeCollector()

    generateStatementSequenceCode(
        statement_sequence=context.getOwner().subnode_body,
        allow_none=True,
        emit=function_codes,
        context=context,
    )

    function_cleanup = finalizeFunctionLocalVariables(context)

    if needs_exception_exit:
        (
            exception_state_name,
            _exception_lineno,
        ) = context.variable_storage.getExceptionVariableDescriptions()

        generator_exit = template_generator_exception_exit % {
            "function_cleanup": indented(function_cleanup),
            "exception_state_name": exception_state_name,
        }
    else:
        generator_exit = template_generator_noexception_exit % {
            "function_cleanup": indented(function_cleanup)
        }

    if needs_generator_return:
        generator_exit += template_generator_return_exit % {
            "return_value": (
                context.getReturnValueName() if python_version >= 0x300 else None
            ),
            "function_cleanup": indented(function_cleanup),
        }

    function_locals = context.variable_storage.makeCFunctionLevelDeclarations()

    local_type_decl = context.variable_storage.makeCStructLevelDeclarations()
    function_locals += context.variable_storage.makeCStructInits()

    generator_object_body = context.getOwner()

    if local_type_decl:
        heap_declaration = """\
struct %(function_identifier)s_locals *generator_heap = \
(struct %(function_identifier)s_locals *)generator->m_heap_storage;""" % {
            "function_identifier": function_identifier
        }
    else:
        heap_declaration = ""

    generator_creation_args = getFunctionCreationArgs(
        defaults_name=None,
        kw_defaults_name=None,
        annotations_name=None,
        closure_variables=closure_variables,
    )

    return template_generator_context_body_template % {
        "function_identifier": function_identifier,
        "function_body": indented(function_codes.codes),
        "heap_declaration": indented(heap_declaration),
        "has_heap_declaration": 1 if heap_declaration != "" else 0,
        "function_local_types": indented(local_type_decl),
        "function_var_inits": indented(function_locals),
        "function_dispatch": indented(getYieldReturnDispatchCode(context)),
        "generator_maker_identifier": _getGeneratorMakerIdentifier(function_identifier),
        "generator_creation_args": ", ".join(generator_creation_args),
        "generator_exit": generator_exit,
        "generator_module": getModuleAccessCode(context),
        "generator_name_obj": context.getConstantCode(
            constant=generator_object_body.getFunctionName()
        ),
        "generator_qualname_obj": getFunctionQualnameObj(
            generator_object_body, context
        ),
        "code_identifier": getCodeObjectAccessCode(
            code_object=generator_object_body.getCodeObject(), context=context
        ),
        "closure_name": "closure" if closure_variables else "NULL",
        "closure_count": len(closure_variables),
    }


def generateMakeGeneratorObjectCode(to_name, expression, emit, context):
    generator_object_body = expression.subnode_generator_ref.getFunctionBody()

    closure_variables = expression.getClosureVariableVersions()

    closure_name, closure_copy = getClosureCopyCode(
        closure_variables=closure_variables, context=context
    )

    args = ["tstate"]
    if closure_name:
        args.append(closure_name)

    # Special case empty generators.
    if generator_object_body.subnode_body is None:
        emit(
            template_make_empty_generator
            % {
                "closure_copy": indented(closure_copy, 0, True),
                "to_name": to_name,
                "generator_module": getModuleAccessCode(context),
                "generator_name_obj": context.getConstantCode(
                    constant=generator_object_body.getFunctionName()
                ),
                "generator_qualname_obj": getFunctionQualnameObj(
                    generator_object_body, context
                ),
                "code_identifier": context.getCodeObjectHandle(
                    code_object=generator_object_body.getCodeObject()
                ),
                "closure_name": closure_name if closure_name is not None else "NULL",
                "closure_count": len(closure_variables),
            }
        )
    else:
        emit(
            template_make_generator
            % {
                "generator_maker_identifier": _getGeneratorMakerIdentifier(
                    generator_object_body.getCodeName()
                ),
                "to_name": to_name,
                "args": ", ".join(str(arg) for arg in args),
                "closure_copy": indented(closure_copy, 0, True),
            }
        )

    context.addCleanupTempName(to_name)


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
