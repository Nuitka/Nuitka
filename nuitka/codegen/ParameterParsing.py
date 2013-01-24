#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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

from . import CodeTemplates

from .ConstantCodes import getConstantCode
from .Identifiers import Identifier, DefaultValueIdentifier
from .Indentation import indented

def getParameterEntryPointIdentifier( function_identifier, is_method ):
    if is_method:
        return "_mparse_" + function_identifier
    else:
        return "_fparse_" + function_identifier

def getDirectFunctionEntryPointIdentifier( function_identifier ):
    return "impl_" + function_identifier


def _getParameterParsingCode( context, parameters, function_name, is_method ):
    # There is really no way this could be any less complex, pylint: disable=R0912,R0914

    parameter_parsing_code = "".join(
        [
            "PyObject *_python_par_" + variable.getName() + " = NULL;\n"
            for variable in
            parameters.getAllVariables()[ 1 if is_method else 0 : ]
        ]
    )

    top_level_parameters = parameters.getTopLevelVariables()

    plain_possible_count = len( top_level_parameters ) - parameters.getKwOnlyParameterCount()

    if plain_possible_count > 1 or (not is_method and plain_possible_count > 0):
        parameter_parsing_code += str( CodeTemplates.parse_argument_template_take_counts3 )

    if top_level_parameters:
        parameter_parsing_code += "// Copy given dictionary values to the the respective variables:\n"

    if parameters.getDictStarArgVariable() is not None:
        # In the case of star dict arguments, we need to check what is for it and which arguments
        # with names we have.

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
                "parameter_name"        : variable.getName(),
                "function_name"         : function_name,
            }

            if variable.isParameterVariableKwOnly():
                assign_quick = CodeTemplates.argparse_template_assign_from_dict_parameter_quick_path_kw_only
                assign_slow = CodeTemplates.argparse_template_assign_from_dict_parameter_slow_path_kw_only
            else:
                assign_quick = CodeTemplates.argparse_template_assign_from_dict_parameter_quick_path
                assign_slow = CodeTemplates.argparse_template_assign_from_dict_parameter_slow_path


            quick_path_code += assign_quick % {
                "parameter_name_object"    : parameter_name_object,
                "parameter_assign_from_kw" : indented( parameter_assign_from_kw )
            }

            slow_path_code += assign_slow % {
                "parameter_name_object"    : parameter_name_object,
                "parameter_assign_from_kw" : indented( parameter_assign_from_kw )
            }

        parameter_parsing_code += CodeTemplates.argparse_template_assign_from_dict_parameters % {
            "function_name"         : function_name,
            "parameter_quick_path"  : indented( quick_path_code, 2 ),
            "parameter_slow_path"   : indented( slow_path_code, 2 )
        }

    if parameters.isEmpty():
        parameter_parsing_code += CodeTemplates.template_parameter_function_refuses % {
            "function_name" : function_name,
        }
    else:
        if parameters.getListStarArgVariable() is None:
            check_template = CodeTemplates.parse_argument_template_check_counts_without_list_star_arg
        else:
            check_template = CodeTemplates.parse_argument_template_check_counts_with_list_star_arg

        required_parameter_count = len( top_level_parameters ) - parameters.getDefaultCount() - \
                                   parameters.getKwOnlyParameterCount()

        parameter_parsing_code += check_template % {
            "function_name"             : function_name,
            "top_level_parameter_count" : plain_possible_count,
            "required_parameter_count"  : required_parameter_count,
        }

    if plain_possible_count > 1 or (not is_method and plain_possible_count > 0):
        parameter_parsing_code += CodeTemplates.parse_argument_usable_count % {
            "top_level_parameter_count" : plain_possible_count,
        }

        for count, variable in enumerate( top_level_parameters ):
            # The "self" will already be parsed.
            if is_method and count == 0:
                continue

            if variable.isNestedParameterVariable():
                parameter_parsing_code += CodeTemplates.argparse_template_nested_argument % {
                    "parameter_name"       : variable.getName(),
                    "parameter_position"   : count,
                    "parameter_args_index" : count if not is_method else count-1
                }
            elif not variable.isParameterVariableKwOnly():
                parameter_parsing_code += CodeTemplates.argparse_template_plain_argument % {
                    "function_name"        : function_name,
                    "parameter_name"       : variable.getName(),
                    "parameter_position"   : count,
                    "parameter_args_index" : count if not is_method else count-1
                }

    if parameters.getListStarArgVariable() is not None:
        if is_method:
            max_index = plain_possible_count - 1
        else:
            max_index = plain_possible_count

        parameter_parsing_code += CodeTemplates.parse_argument_template_copy_list_star_args % {
            "list_star_parameter_name"  : parameters.getStarListArgumentName(),
            "top_level_parameter_count" : len( top_level_parameters ) - parameters.getKwOnlyParameterCount(),
            "top_level_max_index"       : max_index
        }

    if parameters.hasDefaultParameters():
        parameter_parsing_code += "// Assign values not given to defaults\n"

        for count, variable in enumerate( parameters.getDefaultParameterVariables() ):
            if not variable.isNestedParameterVariable():
                parameter_parsing_code += CodeTemplates.parse_argument_template_copy_default_value % {
                    "parameter_name"     : variable.getName(),
                    "default_identifier" : DefaultValueIdentifier( count ).getCodeExportRef()
                }


    def unPackNestedParameterVariables( variables, default_variables, recursion ):
        result = ""

        for count, variable in enumerate( variables ):
            if variable.isNestedParameterVariable():
                if recursion == 1 and count < len( default_variables ):
                    assign_source = Identifier(
                        "_python_par_%s ? _python_par_%s : %s" % (
                            variable.getName(),
                            variable.getName(),
                            DefaultValueIdentifier( count ).getCodeExportRef()
                        ),
                        0
                    )
                else:
                    assign_source = Identifier(
                        "_python_par_%s" % variable.getName(),
                        0
                    )

                unpack_code = ""

                child_variables = variable.getTopLevelVariables()

                for count, child_variable in enumerate( child_variables ):
                    unpack_code += CodeTemplates.parse_argument_template_nested_argument_assign % {
                        "parameter_name" : child_variable.getName(),
                        "iter_name"      : variable.getName(),
                        "unpack_count"   : count
                    }

                result += CodeTemplates.parse_argument_template_nested_argument_unpack % {
                    "unpack_source_identifier" : assign_source.getCode(),
                    "parameter_name" : variable.getName(),
                    "unpack_code"    : unpack_code
                }


        for variable in variables:
            if variable.isNestedParameterVariable():
                result += unPackNestedParameterVariables(
                    variables         = variable.getTopLevelVariables(),
                    default_variables = (),
                    recursion         = recursion + 1
                )

        return result

    parameter_parsing_code += unPackNestedParameterVariables(
        variables         = top_level_parameters,
        default_variables = parameters.getDefaultParameterVariables(),
        recursion         = 1
    )

    for variable in parameters.getKwOnlyVariables():
        parameter_parsing_code += CodeTemplates.template_kwonly_argument_default % {
            "function_name"         : function_name,
            "parameter_name"        : variable.getName(),
            "parameter_name_object" : getConstantCode(
                        constant = variable.getName(),
                        context  = context
                    )
        }

    return indented( parameter_parsing_code )

def getParameterParsingCode( context, function_identifier, function_name, parameters,
                             needs_creation ):

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
            context             = context,
            function_name       = function_name,
            parameters          = parameters,
            is_method           = False
        ),
        "parse_function_identifier" : getParameterEntryPointIdentifier(
            function_identifier = function_identifier,
            is_method           = False
        ),
        "impl_function_identifier"  : getDirectFunctionEntryPointIdentifier(
            function_identifier = function_identifier
        ),
        "parameter_objects_list"    : ", ".join( parameter_objects_list ),
        "parameter_release_code"    : parameter_release_code,
    }

    # Note: It's only a convention, but one generally adhered, so use the presence of a "self"
    # to detect of a "method" entry point makes sense.
    if function_parameter_variables and function_parameter_variables[0].getName() == "self":
        mparse_identifier = getParameterEntryPointIdentifier(
            function_identifier = function_identifier,
            is_method           = True
        )

        parameter_entry_point_code += CodeTemplates.template_parameter_method_entry_point % {
            "parameter_parsing_code"    : _getParameterParsingCode(
                context             = context,
                function_name       = function_name,
                parameters          = parameters,
                is_method           = True
            ),
            "parse_function_identifier" : mparse_identifier,
            "impl_function_identifier"  : getDirectFunctionEntryPointIdentifier(
                function_identifier = function_identifier
            ),
            "parameter_objects_list"    : ", ".join( parameter_objects_list ),
            "parameter_release_code"    : parameter_release_code
        }
    else:
        mparse_identifier = "NULL"

    return (
        function_parameter_variables,
        parameter_entry_point_code,
        parameter_objects_decl,
        mparse_identifier
    )
