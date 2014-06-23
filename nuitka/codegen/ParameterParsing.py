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
""" Low level code generation for parameter parsing.

"""

from nuitka.Utils import python_version

from . import CodeTemplates
from .ConstantCodes import getConstantCode
from .Indentation import indented


def getParameterEntryPointIdentifier(function_identifier):
    return "fparse_" + function_identifier


def getQuickEntryPointIdentifier(function_identifier, parameters):
    if parameters.hasNestedParameterVariables() or \
       parameters.getKwOnlyParameterCount() > 0:
        return "NULL"
    else:
        return "dparse_" + function_identifier


def getDirectFunctionEntryPointIdentifier(function_identifier):
    return "impl_" + function_identifier


def _getParameterParsingCode(context, parameters, function_name):
    # There is really no way this could be any less complex.
    # pylint: disable=R0912,R0914

    # First, declare all parameter objects as variables.
    parameter_parsing_code = "".join(
        [
            "PyObject *_python_par_" + variable.getName() + " = NULL;\n"
            for variable in
            parameters.getAllVariables()
        ]
    )

    top_level_parameters = parameters.getTopLevelVariables()

    # Max allowed number of positional arguments, all except keyword only
    # arguments.
    plain_possible_count = len( top_level_parameters ) - \
                           parameters.getKwOnlyParameterCount()

    if top_level_parameters:
        parameter_parsing_code += "// Copy given dictionary values to the the respective variables:\n"

    if parameters.getDictStarArgVariable() is not None:
        # In the case of star dict arguments, we need to check what is for it
        # and which arguments with names we have.

        parameter_parsing_code += CodeTemplates.parse_argument_template_dict_star_copy % {
            "dict_star_parameter_name" : parameters.getStarDictArgumentName(),
            "function_name"            : function_name,
        }

        # Check for each variable.
        for variable in top_level_parameters:
            if not variable.isNestedParameterVariable():
                parameter_parsing_code += CodeTemplates.parse_argument_template_check_dict_parameter_with_star_dict % {
                    "parameter_name"           : variable.getName(),
                    "parameter_name_object"    : getConstantCode(
                        constant = variable.getName(),
                        context  = context
                    ),
                    "dict_star_parameter_name" : parameters.getStarDictArgumentName(),
                }
    elif not parameters.isEmpty():
        quick_path_code = ""
        slow_path_code = ""

        for variable in top_level_parameters:
            # Only named ones can be assigned from the dict.
            if variable.isNestedParameterVariable():
                continue

            parameter_name_object = getConstantCode(
                constant = variable.getName(),
                context  = context
            )

            parameter_assign_from_kw = CodeTemplates.argparse_template_assign_from_dict_finding % {
                "parameter_name" : variable.getName(),
            }

            if variable.isParameterVariableKwOnly():
                assign_quick = CodeTemplates.argparse_template_assign_from_dict_parameter_quick_path_kw_only
                assign_slow = CodeTemplates.argparse_template_assign_from_dict_parameter_slow_path_kw_only
            else:
                assign_quick = CodeTemplates.argparse_template_assign_from_dict_parameter_quick_path
                assign_slow = CodeTemplates.argparse_template_assign_from_dict_parameter_slow_path


            quick_path_code += assign_quick % {
                "parameter_name_object"    : parameter_name_object,
                "parameter_assign_from_kw" : indented(parameter_assign_from_kw)
            }

            slow_path_code += assign_slow % {
                "parameter_name_object"    : parameter_name_object,
                "parameter_assign_from_kw" : indented(parameter_assign_from_kw)
            }

        parameter_parsing_code += CodeTemplates.argparse_template_assign_from_dict_parameters % {
            "function_name"         : function_name,
            "parameter_quick_path"  : indented(quick_path_code, 2),
            "parameter_slow_path"   : indented(slow_path_code, 2)
        }

    if parameters.isEmpty():
        parameter_parsing_code += CodeTemplates.template_parameter_function_refuses % {}
    elif python_version < 330:
        if parameters.getListStarArgVariable() is None:
            parameter_parsing_code += CodeTemplates.parse_argument_template_check_counts_without_list_star_arg % {
                "top_level_parameter_count" : plain_possible_count,
            }

    if plain_possible_count > 0:
        plain_var_names = []

        parameter_parsing_code += CodeTemplates.parse_argument_usable_count % {}

        for count, variable in enumerate( top_level_parameters ):
            if variable.isNestedParameterVariable():
                parameter_parsing_code += CodeTemplates.argparse_template_nested_argument % {
                    "parameter_name"            : variable.getName(),
                    "parameter_position"        : count,
                    "top_level_parameter_count" : plain_possible_count,
                }
            elif not variable.isParameterVariableKwOnly():
                parameter_parsing_code += CodeTemplates.argparse_template_plain_argument % {
                    "parameter_name"            : variable.getName(),
                    "parameter_position"        : count,
                    "top_level_parameter_count" : plain_possible_count,
                }

                plain_var_names.append( "_python_par_" + variable.getName() )

        parameter_parsing_code += CodeTemplates.template_arguments_check % {
            "parameter_test" : " || ".join(
                "%s == NULL" % plain_var_name
                for plain_var_name in
                plain_var_names
            ),
            "parameter_list" : ", ".join( plain_var_names )
        }


    if parameters.getListStarArgVariable() is not None:
        parameter_parsing_code += CodeTemplates.parse_argument_template_copy_list_star_args % {
            "list_star_parameter_name"  : parameters.getStarListArgumentName(),
            "top_level_parameter_count" : plain_possible_count
        }
    elif python_version >= 330:
        parameter_parsing_code += CodeTemplates.parse_argument_template_check_counts_without_list_star_arg % {
            "top_level_parameter_count" : plain_possible_count,
        }

    def unPackNestedParameterVariables(variables):
        result = ""

        for count, variable in enumerate( variables ):
            if variable.isNestedParameterVariable():
                assign_source = "_python_par_%s" % variable.getName()

                unpack_code = ""

                child_variables = variable.getTopLevelVariables()

                for count, child_variable in enumerate( child_variables ):
                    unpack_code += CodeTemplates.parse_argument_template_nested_argument_assign % {
                        "parameter_name" : child_variable.getName(),
                        "iter_name"      : variable.getName(),
                        "unpack_count"   : count
                    }

                result += CodeTemplates.parse_argument_template_nested_argument_unpack % {
                    "unpack_source_identifier" : assign_source,
                    "parameter_name" : variable.getName(),
                    "unpack_code"    : unpack_code
                }


        for variable in variables:
            if variable.isNestedParameterVariable():
                result += unPackNestedParameterVariables(
                    variables = variable.getTopLevelVariables()
                )

        return result

    parameter_parsing_code += unPackNestedParameterVariables(
        variables = top_level_parameters
    )

    kw_only_var_names = []

    for variable in parameters.getKwOnlyVariables():
        parameter_parsing_code += CodeTemplates.template_kwonly_argument_default % {
            "function_name"         : function_name,
            "parameter_name"        : variable.getName(),
            "parameter_name_object" : getConstantCode(
                constant = variable.getName(),
                context  = context
            )
        }

        kw_only_var_names.append( "_python_par_" + variable.getName() )

    if kw_only_var_names:
        parameter_parsing_code += CodeTemplates.template_kwonly_arguments_check % {
            "parameter_test" : " || ".join(
                "%s == NULL" % kw_only_var_name
                for kw_only_var_name in
                kw_only_var_names
            ),
            "parameter_list" : ", ".join( kw_only_var_names )
        }

    return indented( parameter_parsing_code )

def getParameterParsingCode( context, function_identifier, function_name,
                             parameters, needs_creation ):

    function_parameter_variables = parameters.getVariables()

    if function_parameter_variables:
        parameter_objects_decl = [
            "PyObject *_python_par_" + variable.getName()
            for variable in
            function_parameter_variables
        ]

        parameter_objects_list = [
            "_python_par_" + variable.getName()
            for variable in
            function_parameter_variables
        ]
    else:
        parameter_objects_decl = []
        parameter_objects_list = []

    if needs_creation:
        parameter_objects_decl.insert( 0, "Nuitka_FunctionObject *self" )
        parameter_objects_list.insert( 0, "self" )

    parameter_release_code = "".join(
        [
            "    Py_XDECREF( _python_par_" + variable.getName() + " );\n"
            for variable in
            parameters.getAllVariables()
            if not variable.isNestedParameterVariable()
        ]
    )

    parameter_entry_point_code = CodeTemplates.template_parameter_function_entry_point % {
        "parameter_parsing_code"    : _getParameterParsingCode(
            context       = context,
            function_name = function_name,
            parameters    = parameters,

        ),
        "parse_function_identifier" : getParameterEntryPointIdentifier(
            function_identifier = function_identifier,
        ),
        "impl_function_identifier"  : getDirectFunctionEntryPointIdentifier(
            function_identifier = function_identifier
        ),
        "parameter_objects_list"    : ", ".join( parameter_objects_list ),
        "parameter_release_code"    : parameter_release_code,
    }

    if not parameters.hasNestedParameterVariables() and \
       not parameters.getKwOnlyParameterCount() > 0:
        args_forward = []

        count = -1
        for count, variable in enumerate( parameters.getTopLevelVariables() ):
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

        parameter_entry_point_code += CodeTemplates.template_dparser % {
            "function_identifier" : function_identifier,
            "arg_count"           : len( function_parameter_variables ),
            "args_forward"        : "".join( args_forward )

        }

    return (
        function_parameter_variables,
        parameter_entry_point_code,
        parameter_objects_decl
    )
