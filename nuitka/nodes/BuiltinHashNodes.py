#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Node the calls to the 'hash' built-in.

This is a specific thing, which must be calculated at run time, but we can
predict things about its type, and the fact that it won't raise an exception
for some types, so it is still useful. Also calls to it can be accelerated
slightly.
"""

from .ExpressionBases import ExpressionChildrenHavingBase


class ExpressionBuiltinHash(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_HASH"

    named_children = (
        "value",
    )

    def __init__(self, value, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "value" : value,
            },
            source_ref = source_ref
        )

    getValue = ExpressionChildrenHavingBase.childGetter(
        "value"
    )

    def computeExpression(self, trace_collection):
        value = self.getValue()

        # TODO: Have a computation slot for hashing.
        if not value.isKnownToBeHashable():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return not self.getValue().isKnownToBeHashable()
