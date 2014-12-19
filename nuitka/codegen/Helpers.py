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
""" Helpers for code generation.

This dispatch building of expressions and (coming) statements, as well as
providing typical support functions to building parts.

"""

expression_dispatch_dict = {}

def setExpressionDispatchDict(values):
    # Please call us only once.
    assert not expression_dispatch_dict

    for key, value in values.items():
        expression_dispatch_dict["EXPRESSION_" + key] = value

def generateExpressionCode(to_name, expression, emit, context):
    if expression.kind in expression_dispatch_dict:
        expression_dispatch_dict[expression.kind](
            to_name    = to_name,
            expression = expression,
            emit       = emit,
            context    = context
        )

        return True
    else:
        return False

def generateChildExpressionsCode(expression, emit, context):
    value_names = []

    for child_name in expression.named_children:
        child_value = expression.getChild(child_name)

        # Allocate anyway, so names are aligned.
        value_name = context.allocateTempName(child_name + "_name")

        if child_value is not None:

            # TODO: This will move to local module, # pylint: disable=W0621
            from .CodeGeneration import generateExpressionCode

            generateExpressionCode(
                to_name    = value_name,
                expression = child_value,
                emit       = emit,
                context    = context
            )

            value_names.append(value_name)
        else:
            context.forgetTempName(value_name)
            value_names.append(None)


    return value_names
