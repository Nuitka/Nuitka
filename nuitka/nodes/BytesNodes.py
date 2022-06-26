#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Nodes that build and operate on bytes (Python3).

"""

from .ConstantRefNodes import makeConstantRefNode
from .ExpressionBases import (
    ExpressionChildHavingBase,
    ExpressionChildrenHavingBase,
)
from .ExpressionShapeMixins import ExpressionStrShapeExactMixin
from .NodeMetaClasses import NodeCheckMetaClass


def getBytesOperationClasses():
    """Return all bytes operation nodes, for use by code generation."""
    return (
        cls
        for kind, cls in NodeCheckMetaClass.kinds.items()
        if kind.startswith("EXPRESSION_BYTES_OPERATION_")
    )


class ExpressionBytesOperationDecodeMixin(ExpressionStrShapeExactMixin):
    __slots__ = ()

    # TODO: Encodings might be registered and influence things at runtime, disabled
    # until we researched that.
    @staticmethod
    def getSimulator():
        """Compile time simulation"""

        return bytes.decode


class ExpressionBytesOperationDecode1(
    ExpressionBytesOperationDecodeMixin, ExpressionChildHavingBase
):
    kind = "EXPRESSION_BYTES_OPERATION_DECODE1"

    named_child = "bytes_arg"

    def __init__(self, bytes_arg, source_ref):
        assert bytes_arg is not None

        ExpressionChildHavingBase.__init__(
            self,
            value=bytes_arg,
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        # TODO: Only if the bytes cannot be decoded.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionBytesOperationDecode2(
    ExpressionBytesOperationDecodeMixin, ExpressionChildrenHavingBase
):
    kind = "EXPRESSION_BYTES_OPERATION_DECODE2"

    named_children = "bytes_arg", "encoding"

    def __init__(self, bytes_arg, encoding, source_ref):
        assert bytes_arg is not None
        assert encoding is not None

        ExpressionChildrenHavingBase.__init__(
            self,
            values={"bytes_arg": bytes_arg, "encoding": encoding},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        # TODO: Only if the bytes cannot be decoded to the given encoding
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionBytesOperationDecode3(
    ExpressionBytesOperationDecodeMixin, ExpressionChildrenHavingBase
):
    kind = "EXPRESSION_BYTES_OPERATION_DECODE3"

    named_children = "bytes_arg", "encoding", "errors"

    def __init__(self, bytes_arg, encoding, errors, source_ref):
        assert bytes_arg is not None
        assert errors is not None

        if encoding is None:
            encoding = makeConstantRefNode(constant="utf-8", source_ref=source_ref)

        ExpressionChildrenHavingBase.__init__(
            self,
            values={"bytes_arg": bytes_arg, "encoding": encoding, "errors": errors},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        # TODO: Only if the bytes cannot be decoded to the given encoding, and errors
        # is not ignore.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None
