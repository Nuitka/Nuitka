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


from nuitka.nodes.BuiltinTypeNodes import ExpressionBuiltinStr
from nuitka.nodes.PrintNodes import StatementPrint

from .Helpers import (
    buildNodeList,
    buildNode
)

def buildPrintNode(provider, node, source_ref):
    # "print" statements, should only occur with Python2.

    values = buildNodeList( provider, node.values, source_ref )

    def wrapValue(value):
        if value.isExpressionConstantRef():
            return value.getStrValue()
        else:
            return ExpressionBuiltinStr(
                value      = value,
                source_ref = value.getSourceReference()
            )


    values = [
        wrapValue( value )
        for value in
        values
    ]

    return StatementPrint(
        newline    = node.nl,
        dest       = buildNode(
            provider   = provider,
            node       = node.dest,
            source_ref = source_ref,
            allow_none = True
        ),
        values     = values,
        source_ref = source_ref
    )
