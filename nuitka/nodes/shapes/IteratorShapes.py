#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Iterator shapes that commonly appear. """

from .ControlFlowDescriptions import ControlFlowDescriptionFullEscape
from .ShapeMixins import ShapeIteratorMixin
from .StandardShapes import ShapeBase, tshape_unknown


class ShapeIterator(ShapeBase, ShapeIteratorMixin):
    """Iterator created by iter with 2 arguments, TODO: could be way more specific."""

    __slots__ = ()

    @staticmethod
    def isShapeIterator():
        return None

    @staticmethod
    def hasShapeSlotBool():
        return None

    @staticmethod
    def hasShapeSlotLen():
        return None

    @staticmethod
    def hasShapeSlotInt():
        return None

    @staticmethod
    def hasShapeSlotLong():
        return None

    @staticmethod
    def hasShapeSlotFloat():
        return None

    @staticmethod
    def getShapeIter():
        return tshape_iterator

    @staticmethod
    def getOperationUnaryReprEscape():
        return ControlFlowDescriptionFullEscape

    def getOperationUnaryAddShape(self):
        # TODO: Move prepared values to separate module
        return tshape_unknown, ControlFlowDescriptionFullEscape

    def getOperationUnarySubShape(self):
        return tshape_unknown, ControlFlowDescriptionFullEscape


tshape_iterator = ShapeIterator()

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
