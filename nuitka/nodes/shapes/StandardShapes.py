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
""" Standard shapes that commonly appear. """
from nuitka.codegen.c_types.CTypePyObjectPtrs import CTypePyObjectPtr


class ShapeBase(object):
    @staticmethod
    def getShapeIter():
        return ShapeUnknown

    @staticmethod
    def getTypeName():
        return None

    @staticmethod
    def hasShapeModule():
        return False

    @staticmethod
    def getCType():
        return CTypePyObjectPtr

    @staticmethod
    def hasShapeSlotBytes():
        return None


class ShapeUnknown(ShapeBase):
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
    def hasShapeSlotComplex():
        return None

    @staticmethod
    def hasShapeSlotIter():
        return None

    @staticmethod
    def hasShapeSlotNext():
        return None

    @staticmethod
    def hasShapeSlotContains():
        return None

    @staticmethod
    def hasShapeSlotBytes():
        return None


class ValueShapeBase(object):
    __slots__ = ()

    def hasShapeSlotLen(self):
        return self.getTypeShape().hasShapeSlotLen()


class ValueShapeUnknown(ValueShapeBase):
    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return ShapeUnknown

# Singleton value for sharing.
vshape_unknown = ValueShapeUnknown()


class ShapeLargeConstantValue(object):
    __slots__ = "shape", "size"

    def __init__(self, size, shape):
        self.size = size
        self.shape = shape

    def getTypeShape(self):
        return self.shape

    @staticmethod
    def isConstant():
        return True

    def hasShapeSlotLen(self):
        return self.shape.hasShapeSlotLen()


class ShapeLargeConstantValuePredictable(ShapeLargeConstantValue):
    __slots__ = ("predictor",)

    def __init__(self, size, predictor, shape):
        ShapeLargeConstantValue.__init__(self, size, shape)

        self.predictor = predictor


class ShapeIterator(ShapeBase):
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
    def hasShapeSlotIter():
        return True

    @staticmethod
    def hasShapeSlotNext():
        return True

    @staticmethod
    def getShapeIter():
        return ShapeIterator

    @staticmethod
    def hasShapeSlotContains():
        return True
