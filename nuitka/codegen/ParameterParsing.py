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
""" Low level code generation for parameter parsing.

"""

from .Indentation import indented
from .templates.CodeTemplatesParameterParsing import (
    template_parameter_dparser_entry_point,
    template_parameter_function_entry_point
)


def getParameterEntryPointIdentifier(function_identifier):
    return "fparse_" + function_identifier


def getQuickEntryPointIdentifier(function_identifier, parameters):
    if parameters.getKwOnlyParameterCount() > 0:
        return "NULL"
    else:
        return "dparse_" + function_identifier


def getDirectFunctionEntryPointIdentifier(function_identifier):
    return "impl_" + function_identifier


def _getParameterParsingCode(all_parameter_variables):
    all_variable_count = len(all_parameter_variables)

    # First, declare all parameter objects as variables.
    parameter_parsing_code = """
PyObject *python_pars[ %(arg_count)d ] = { %(arg_init)s };
""" % {
        "arg_count" : all_variable_count or 1, # MSVC disallows 0.
        "arg_init"  : ", ".join(["NULL"] * (all_variable_count or 1))
    }

    return indented(parameter_parsing_code)


def getParameterParsingCode(function_identifier, parameters, needs_creation):
    if parameters is None:
        all_parameter_variables = ()
    else:
        all_parameter_variables = parameters.getAllVariables()

    if all_parameter_variables:
        parameter_objects_decl = [
            "PyObject *_python_par_" + variable.getCodeName()
            for variable in
            all_parameter_variables
        ]

        parameter_objects_list = [
            "python_pars[%d]" % arg_index
            for arg_index in
            range(len(all_parameter_variables))
        ]
    else:
        parameter_objects_decl = []
        parameter_objects_list = []

    if needs_creation:
        parameter_objects_decl.insert(0, "Nuitka_FunctionObject *self")
        parameter_objects_list.insert(0, "self")

    parameter_entry_point_code = template_parameter_function_entry_point % {
        "parameter_parsing_code"    : _getParameterParsingCode(
            all_parameter_variables = all_parameter_variables,
        ),
        "parse_function_identifier" : getParameterEntryPointIdentifier(
            function_identifier = function_identifier,
        ),
        "impl_function_identifier"  : getDirectFunctionEntryPointIdentifier(
            function_identifier = function_identifier
        ),
        "parameter_objects_list"    : ", ".join(parameter_objects_list),
    }

    if parameters is not None and \
       parameters.getKwOnlyParameterCount() == 0:
        args_forward = []

        count = -1
        for count, variable in enumerate(parameters.getTopLevelVariables()):
            args_forward.append(
                ", INCREASE_REFCOUNT( args[ %d ] )" % count
            )

        if parameters.getListStarArgVariable() is not None:
            count += 1

            args_forward.append(
                ", MAKE_TUPLE( &args[ %d ], size > %d ? size-%d : 0 )" % (
                    count, count, count
                )
            )

        if parameters.getDictStarArgVariable() is not None:
            args_forward.append(
                ", PyDict_New()"
            )

        # print args_forward

        parameter_entry_point_code += template_parameter_dparser_entry_point % {
            "function_identifier" : function_identifier,
            "arg_count"           : len(all_parameter_variables),
            "args_forward"        : "".join(args_forward)

        }

    return (
        all_parameter_variables,
        parameter_entry_point_code,
        parameter_objects_decl
    )
