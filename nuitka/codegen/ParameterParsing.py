#
#     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#
""" Low level code generation for parameter parsing.

"""

from . import CodeTemplates

from .ConstantCodes import getConstantCode
from .VariableCodes import getVariableCode

from .Identifiers import Identifier

from .Indentation import indented

def _getDefaultParameterCodeName( variable ):
    if variable.isNestedParameterVariable():
        return "default_values_%s" % "__".join( variable.getParameterNames() )
    else:
        return "default_value_%s" % variable.getName()

def getDefaultParameterDeclarations( default_identifiers ):
    return [
        "PyObject *%s" % default_identifier.getCode().split( "->" )[1]
        for default_identifier in default_identifiers
        if "->" in default_identifier.getCode()
    ]

def getParameterEntryPointIdentifier( function_identifier, is_method ):
    if is_method:
        return "_mparse_" + function_identifier
    else:
        return "_fparse_" + function_identifier

def getParameterContextCode( default_access_identifiers ):
    context_decl = []
    context_copy = []
    context_free = []

    for default_access_identifier in default_access_identifiers:
        default_par_code = default_access_identifier.getCode()

        if "->" in default_par_code:
            default_par_code_name = default_par_code.split("->")[1]

            context_decl.append(
                "PyObject *%s;" % default_par_code_name
            )
            context_copy.append(
                "_python_context->%s = %s;" % (
                    default_par_code_name,
                    default_par_code_name
                )
            )
            context_free.append(
                "Py_DECREF( _python_context->%s );" % default_par_code_name
            )

    # print default_access_identifiers, context_decl, context_copy, context_free

    return context_decl, context_copy, context_free


def _getParameterParsingCode( context, parameters, function_name, default_identifiers, is_method ):
    parameter_parsing_code = "".join(
        [
            "PyObject *_python_par_" + variable.getName() + " = NULL;\n"
            for variable in
            parameters.getAllVariables()[ 0 if not is_method else 1 : ]
        ]
    )

    top_level_parameters = parameters.getTopLevelVariables()

    if top_level_parameters and parameters.getDictStarArgVariable() is None:
        parameter_parsing_code += CodeTemplates.parse_argument_template_take_counts2

    if top_level_parameters:
        parameter_parsing_code += CodeTemplates.parse_argument_template_take_counts3

    if parameters.isEmpty():
        parameter_parsing_code += CodeTemplates.template_parameter_function_refuses % {
            "function_name" : function_name,
        }
    else:
        if top_level_parameters and parameters.getDictStarArgVariable() is None:
            parameter_parsing_code += CodeTemplates.parse_argument_template_check_dict_parameter_unused_without_star_dict % {
                "function_name"         : function_name,
                "parameter_names_tuple" : getConstantCode(
                    context  = context,
                    constant = tuple(
                        variable.getName()
                        for variable in
                        parameters.getVariables()
                    )
                )
            }

        if parameters.getListStarArgVariable() is None:
            check_template = CodeTemplates.parse_argument_template_check_counts_without_list_star_arg
        else:
            check_template = CodeTemplates.parse_argument_template_check_counts_with_list_star_arg

        required_parameter_count = len( top_level_parameters ) - parameters.getDefaultParameterCount()

        parameter_parsing_code += check_template % {
            "function_name"             : function_name,
            "top_level_parameter_count" : len( top_level_parameters ),
            "required_parameter_count"  : required_parameter_count,
        }

    if top_level_parameters:
        parameter_parsing_code += CodeTemplates.parse_argument_usable_count % {
            "top_level_parameter_count" : len( top_level_parameters ),
        }

        for count, variable in enumerate( top_level_parameters ):
            if is_method and count == 0:
                continue

            # TODO: These templates really have no sensible names at all.
            if variable.isNestedParameterVariable():
                parse_argument_template2 = CodeTemplates.parse_argument_template2a
            else:
                parse_argument_template2 = CodeTemplates.parse_argument_template2

            parameter_parsing_code += parse_argument_template2 % {
                "parameter_name"       : variable.getName(),
                "parameter_position"   : count,
                "parameter_args_index" : count if not is_method else count-1
            }

    if parameters.getListStarArgVariable() is not None:
        parameter_parsing_code += CodeTemplates.parse_argument_template_copy_list_star_args % {
            "list_star_parameter_name"  : parameters.getListStarArgName(),
            "top_level_parameter_count" : len( top_level_parameters ),
            "top_level_max_index"       : len( top_level_parameters ) if not is_method else len( top_level_parameters ) - 1
        }

    if top_level_parameters:
        parameter_parsing_code += "// Copy given dictionary values to the the respective variables\n"

    if parameters.getDictStarArgVariable() is not None:
        parameter_parsing_code += CodeTemplates.parse_argument_template_dict_star_copy % {
            "dict_star_parameter_name" : parameters.getDictStarArgName(),
        }

        for variable in top_level_parameters:
            if not variable.isNestedParameterVariable():
                parameter_parsing_code += CodeTemplates.parse_argument_template_check_dict_parameter_with_star_dict % {
                    "function_name"            : function_name,
                    "parameter_name"           : variable.getName(),
                    "parameter_name_object"    : getConstantCode(
                        constant = variable.getName(),
                        context  = context
                    ),
                    "dict_star_parameter_name" : parameters.getDictStarArgName(),
                }
    else:
        for variable in top_level_parameters:
            if not variable.isNestedParameterVariable():
                parameter_parsing_code += CodeTemplates.parse_argument_template_check_dict_parameter_without_star_dict % {
                    "function_name"         : function_name,
                    "parameter_name"        : variable.getName(),
                    "parameter_identifier"  : getVariableCode(
                        variable = variable,
                        context = context
                    ),
                    "parameter_name_object" : getConstantCode(
                        constant = variable.getName(),
                        context  = context
                    )
                }

    if parameters.hasDefaultParameters():
        parameter_parsing_code += "// Assign values not given to defaults\n"

        for count, variable in enumerate( parameters.getDefaultParameterVariables() ):
            if not variable.isNestedParameterVariable():
                parameter_parsing_code += CodeTemplates.parse_argument_template_copy_default_value % {
                    "parameter_name"     : variable.getName(),
                    "default_identifier" : default_identifiers[ count ].getCodeExportRef()
                }


    def unPackNestedParameterVariables( variables, default_identifiers, recursion ):
        result = ""

        for count, variable in enumerate( variables ):
            if variable.isNestedParameterVariable():
                if recursion == 1 and count < len( default_identifiers ):
                    assign_source = Identifier(
                        "_python_par_%s ? _python_par_%s : %s" % (
                            variable.getName(),
                            variable.getName(),
                            default_identifiers[ count ].getCode()
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
                    variables           = variable.getTopLevelVariables(),
                    default_identifiers = (),
                    recursion           = recursion + 1
                )

        return result

    parameter_parsing_code += unPackNestedParameterVariables(
        variables           = top_level_parameters,
        default_identifiers = default_identifiers,
        recursion           = 1
    )

    return indented( parameter_parsing_code )

def getParameterParsingCode( context, function_identifier, function_name, parameters, default_identifiers, context_access_template ):
    if getDefaultParameterDeclarations( default_identifiers ):
        context_access = context_access_template % {
            "function_identifier" : function_identifier
        }
    else:
        context_access = ""

    function_parameter_variables = parameters.getVariables()

    if function_parameter_variables:
        parameter_objects_decl = ", " + ", ".join(
            [
                "PyObject *_python_par_" + variable.getName()
                for variable in
                function_parameter_variables
            ]
        )

        parameter_objects_list = ", " + ", ".join(
            [
                "_python_par_" + variable.getName()
                for variable in
                function_parameter_variables
            ]
        )
    else:
        parameter_objects_decl = ""
        parameter_objects_list = ""

    parameter_release_code = "".join(
        [
            "    Py_XDECREF( _python_par_" + variable.getName() + " );\n"
            for variable in
            parameters.getAllVariables()
            if not variable.isNestedParameterVariable()
        ]
    )

    parameter_entry_point_code = CodeTemplates.template_parameter_function_entry_point % {
        "parameter_parsing_code" : _getParameterParsingCode(
            context             = context,
            function_name       = function_name,
            parameters          = parameters,
            default_identifiers = default_identifiers,
            is_method           = False
        ),
        "parse_function_identifier" : getParameterEntryPointIdentifier( function_identifier, False ),
        "impl_function_identifier"  : "impl_" + function_identifier,
        "context_access"         : context_access,
        "parameter_objects_list" : parameter_objects_list,
        "parameter_release_code" : parameter_release_code,
    }

    if function_parameter_variables and function_parameter_variables[0].getName() == "self":
        mparse_identifier = getParameterEntryPointIdentifier( function_identifier, True )

        parameter_entry_point_code += CodeTemplates.template_parameter_method_entry_point % {
            "parameter_parsing_code" : _getParameterParsingCode(
                context             = context,
                function_name       = function_name,
                parameters          = parameters,
                default_identifiers = default_identifiers,
                is_method           = True
            ),
            "parse_function_identifier" : mparse_identifier,
            "impl_function_identifier"  : "impl_" + function_identifier,
            "context_access"         : context_access,
            "parameter_objects_list" : parameter_objects_list,
            "parameter_release_code" : parameter_release_code
        }
    else:
        mparse_identifier = "NULL"


    return (
        function_parameter_variables,
        parameter_entry_point_code,
        parameter_objects_decl,
        mparse_identifier
    )
