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
""" Generate code that enforces ordered evaluation.

"""

from .Identifiers import (
    getCodeTemporaryRefs,
    getCodeExportRefs,
    Identifier
)

from .Indentation import getBlockCode

def getLineNumberCode( line_number ):
    return "frame_guard.setLineNumber( %d )" % line_number

def pickFirst( order_relevance ):
    for value in order_relevance:
        if value:
            return value
    else:
        return None

def _getAssignmentTempKeeperCode( source_identifier, variable_name, context ):
    ref_count = source_identifier.getCheapRefCount()

    context.addTempKeeperUsage( variable_name, ref_count )

    return Identifier(
        "%s.assign( %s )" % (
            variable_name,
            source_identifier.getCodeExportRef()
              if ref_count else
            source_identifier.getCodeTemporaryRef()
        ),
        0
    )


def getOrderRelevanceEnforcedArgsCode( helper, tmp_scope, order_relevance, args,
                                       export_ref, context, ref_count,
                                       prefix_args = None, suffix_args = None ):

    if prefix_args is None:
        prefix_args = []

    if suffix_args is None:
        suffix_args = []

    assert len( args ) == len( order_relevance )

    if order_relevance.count( None ) <= len( args ) - 2:
        order_relevance, lines = _getMinimalOrderRelevance( order_relevance )

        assert len( args ) == len( lines )

        order_codes = []
        arg_codes = []

        for argument, order_relevant, line in zip(
                args, order_relevance, lines ):
            variable_name = "%s%d" % (
                tmp_scope,
                context.allocateCallTempNumber()
            )

            if line:
                order_codes.append(
                    getLineNumberCode( line )
                )

            if order_relevant:
                order_codes.append(
                    _getAssignmentTempKeeperCode(
                        source_identifier = argument,
                        variable_name     = variable_name,
                        context           = context
                    ).getCode()
                )

                if export_ref:
                    arg_codes.append( variable_name + ".asObject()" )
                else:
                    arg_codes.append( variable_name + ".asObject0()" )
            else:
                # TODO: Should delete the reference immediately after call, if
                # ref_count = 1
                if export_ref:
                    arg_codes.append( argument.getCodeExportRef() )
                else:
                    arg_codes.append( argument.getCodeTemporaryRef() )


        order_codes.append(
            "%s( %s )" % (
                helper,
                ", ".join( list(prefix_args) + arg_codes + list(suffix_args) )
            )
        )

        code = "( %s )" % ", ".join( order_codes )

        if ref_count is None:
            return code
        else:
            return Identifier(
                code,
                ref_count = ref_count
            )
    else:
        if export_ref:
            arg_codes = getCodeExportRefs( args )
        else:
            arg_codes = getCodeTemporaryRefs( args )

        code = "%s( %s )" % (
            helper,
            ", ".join( list(prefix_args) + arg_codes + list(suffix_args) )
        )

        if ref_count is None:
            return code
        else:
            return Identifier(
                code,
                ref_count
            )

def _getMinimalOrderRelevance( order_relevance ):
    last_true = None

    lines = []
    last_line = None

    for count, value in enumerate( order_relevance ):
        if value:
            last_true = count

            if value.shallSetCurrentLine():
                line = value.getLineNumber()

                if last_line != line:
                    last_line = line

                    lines.append( line )
                else:
                    lines.append( None )
            else:
                lines.append( None )
        else:
            lines.append( None )

    if last_true is not None:
        new_order_relevance = list( order_relevance )
        new_order_relevance[ last_true ] = None
        order_relevance = new_order_relevance

    return order_relevance, lines

def _getTempDeclCode( order_relevance, names, values ):
    assert len( names ) == len( values )
    assert len( names ) == len( order_relevance )

    order_relevance, lines = _getMinimalOrderRelevance( order_relevance )

    usages = []
    decls = []
    scoped = False

    for name, value, order_relevant, line in zip( names, values,
                                                  order_relevance, lines ):
        if line:
            decls.append(
                getLineNumberCode( line ) + ";"
            )

        if not order_relevant:
            usages.append( value.getCodeTemporaryRef() )
        else:
            scoped = True

            tmp_name = "tmp_" + name

            if value.getRefCount() == 1:
                decls.append(
                    "PyObjectTemporary %s( %s );" % (
                        tmp_name,
                        value.getCodeExportRef()
                    )
                )

                usages.append( tmp_name + ".asObject()" )
            else:
                decls.append(
                    "PyObject *%s = %s;" % (
                        tmp_name,
                        value.getCodeTemporaryRef()
                    )
                )

                usages.append( tmp_name )

    return scoped, decls, usages

def getOrderRelevanceEnforcedCallCode( helper, order_relevance, names, values ):
    scoped, decls, usages = _getTempDeclCode( order_relevance, names, values )

    if decls:
        code = decls + [ "%s( %s );" % ( helper, ", ".join( usages ) ) ]

        if scoped:
            return getBlockCode(
                code
            )
        else:
            return "\n".join( code )
    else:
        return "%s( %s );" % ( helper, ", ".join( usages ) )
