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
""" Shapes for Python built-in types.

"""

from nuitka.codegen.c_types.CTypeNuitkaBools import CTypeNuitkaBoolEnum
from nuitka.PythonVersions import python_version

from .StandardShapes import ShapeBase, ShapeIterator


class ShapeTypeNoneType(ShapeBase):
    @staticmethod
    def getTypeName():
        return "NoneType"

    @staticmethod
    def hasShapeSlotLen():
        return False

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotContains():
        return False


class ShapeTypeBool(ShapeBase):
    @staticmethod
    def getTypeName():
        return "bool"

    @staticmethod
    def getCType():
        # enum: "0: False", "1": True, "2": unassigned
        return CTypeNuitkaBoolEnum

    @staticmethod
    def hasShapeSlotLen():
        return False

    @staticmethod
    def hasShapeSlotInt():
        return True

    @staticmethod
    def hasShapeSlotLong():
        return True

    @staticmethod
    def hasShapeSlotFloat():
        return True

    @staticmethod
    def hasShapeSlotComplex():
        return True

    @staticmethod
    def hasShapeSlotIter():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotContains():
        return False


class ShapeTypeInt(ShapeBase):
    @staticmethod
    def getTypeName():
        return "int"

    @staticmethod
    def hasShapeSlotLen():
        return False

    @staticmethod
    def hasShapeSlotInt():
        return True

    @staticmethod
    def hasShapeSlotLong():
        return True

    @staticmethod
    def hasShapeSlotFloat():
        return True

    @staticmethod
    def hasShapeSlotComplex():
        return True

    @staticmethod
    def hasShapeSlotIter():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotContains():
        return False


class ShapeTypeLong(ShapeBase):
    @staticmethod
    def getTypeName():
        return "long"

    @staticmethod
    def hasShapeSlotLen():
        return False

    @staticmethod
    def hasShapeSlotInt():
        return True

    @staticmethod
    def hasShapeSlotLong():
        return True

    @staticmethod
    def hasShapeSlotFloat():
        return True

    @staticmethod
    def hasShapeSlotComplex():
        return True

    @staticmethod
    def hasShapeSlotIter():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotContains():
        return False


if python_version < 300:
    class ShapeTypeIntOrLong(ShapeBase):
        @staticmethod
        def hasShapeSlotLen():
            return False

        @staticmethod
        def hasShapeSlotInt():
            return True

        @staticmethod
        def hasShapeSlotLong():
            return True

        @staticmethod
        def hasShapeSlotFloat():
            return True

        @staticmethod
        def hasShapeSlotComplex():
            return True

        @staticmethod
        def hasShapeSlotIter():
            return False

        @staticmethod
        def hasShapeSlotNext():
            return False

        @staticmethod
        def hasShapeSlotContains():
            return False
else:
    ShapeTypeIntOrLong = ShapeTypeInt


class ShapeTypeFloat(ShapeBase):
    @staticmethod
    def getTypeName():
        return "float"

    @staticmethod
    def hasShapeSlotLen():
        return False

    @staticmethod
    def hasShapeSlotInt():
        return True

    @staticmethod
    def hasShapeSlotLong():
        return True

    @staticmethod
    def hasShapeSlotFloat():
        return True

    @staticmethod
    def hasShapeSlotComplex():
        return True

    @staticmethod
    def hasShapeSlotIter():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotContains():
        return False


class ShapeTypeComplex(ShapeBase):
    @staticmethod
    def getTypeName():
        return "complex"

    @staticmethod
    def hasShapeSlotLen():
        return False

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return True

    @staticmethod
    def hasShapeSlotIter():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotContains():
        return False


class ShapeTypeTuple(ShapeBase):
    @staticmethod
    def getTypeName():
        return "tuple"

    @staticmethod
    def hasShapeSlotLen():
        return True

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return True

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def getShapeIter():
        return ShapeTypeTupleIterator

    @staticmethod
    def hasShapeSlotContains():
        return True


class ShapeTypeTupleIterator(ShapeIterator):
    @staticmethod
    def getTypeName():
        return "tupleiterator" if python_version < 300 else "tuple_iterator"

    @staticmethod
    def hasShapeSlotLen():
        return False


class ShapeTypeList(ShapeBase):
    @staticmethod
    def getTypeName():
        return "list"

    @staticmethod
    def hasShapeSlotLen():
        return True

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return True

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def getShapeIter():
        return ShapeTypeListIterator

    @staticmethod
    def hasShapeSlotContains():
        return True


class ShapeTypeListIterator(ShapeIterator):
    @staticmethod
    def getTypeName():
        return "listiterator" if python_version < 300 else "list_iterator"

    @staticmethod
    def hasShapeSlotLen():
        return False


class ShapeTypeSet(ShapeBase):
    @staticmethod
    def getTypeName():
        return "set"

    @staticmethod
    def hasShapeSlotLen():
        return True

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return True

    @staticmethod
    def getShapeIter():
        return ShapeTypeSetIterator

    @staticmethod
    def hasShapeSlotContains():
        return True


class ShapeTypeSetIterator(ShapeIterator):
    @staticmethod
    def getTypeName():
        return "setiterator" if python_version < 300 else "set_iterator"

    @staticmethod
    def hasShapeSlotLen():
        return False


class ShapeTypeFrozenset(ShapeBase):
    @staticmethod
    def getTypeName():
        return "frozenset"

    @staticmethod
    def hasShapeSlotLen():
        return True

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return True

    @staticmethod
    def getShapeIter():
        return ShapeTypeSetIterator

    @staticmethod
    def hasShapeSlotContains():
        return True


class ShapeTypeDict(ShapeBase):
    @staticmethod
    def getTypeName():
        return "dict"

    @staticmethod
    def hasShapeSlotLen():
        return True

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return True

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def getShapeIter():
        return ShapeTypeDictIterator

    @staticmethod
    def hasShapeSlotContains():
        return True


class ShapeTypeDictIterator(ShapeIterator):
    @staticmethod
    def getTypeName():
        return "dictionary-keyiterator" if python_version < 300 else "dictkey_iterator"

    @staticmethod
    def hasShapeSlotLen():
        return False


class ShapeTypeStr(ShapeBase):
    @staticmethod
    def getTypeName():
        return "str"

    @staticmethod
    def hasShapeSlotLen():
        return True

    @staticmethod
    def hasShapeSlotInt():
        return True

    @staticmethod
    def hasShapeSlotLong():
        return True

    @staticmethod
    def hasShapeSlotFloat():
        return True

    @staticmethod
    def hasShapeSlotComplex():
        return True

    @staticmethod
    def hasShapeSlotIter():
        return True

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def getShapeIter():
        return ShapeTypeStrIterator

    @staticmethod
    def hasShapeSlotContains():
        return True


class ShapeTypeStrIterator(ShapeIterator):
    @staticmethod
    def getTypeName():
        return "iterator" if python_version < 300 else "str_iterator"

    @staticmethod
    def hasShapeSlotLen():
        return False


if python_version < 300:
    class ShapeTypeUnicode(ShapeBase):
        @staticmethod
        def getTypeName():
            return "unicode"

        @staticmethod
        def hasShapeSlotLen():
            return True

        @staticmethod
        def hasShapeSlotInt():
            return True

        @staticmethod
        def hasShapeSlotLong():
            return True

        @staticmethod
        def hasShapeSlotFloat():
            return True

        @staticmethod
        def hasShapeSlotComplex():
            return True

        @staticmethod
        def hasShapeSlotIter():
            return True

        @staticmethod
        def hasShapeSlotNext():
            return False

        @staticmethod
        def getShapeIter():
            return ShapeTypeUnicodeIterator

        @staticmethod
        def hasShapeSlotContains():
            return True

    class ShapeTypeUnicodeIterator(ShapeIterator):
        @staticmethod
        def getTypeName():
            return "iterator"

        @staticmethod
        def hasShapeSlotLen():
            return False
else:
    ShapeTypeUnicode = ShapeTypeStr
    ShapeTypeUnicodeIterator = ShapeTypeStrIterator

if python_version < 300:
    class ShapeTypeStrOrUnicode(ShapeBase):
        @staticmethod
        def hasShapeSlotLen():
            return True

        @staticmethod
        def hasShapeSlotInt():
            return True

        @staticmethod
        def hasShapeSlotLong():
            return True

        @staticmethod
        def hasShapeSlotFloat():
            return True

        @staticmethod
        def hasShapeSlotComplex():
            return True

        @staticmethod
        def hasShapeSlotIter():
            return True

        @staticmethod
        def hasShapeSlotNext():
            return False

        @staticmethod
        def hasShapeSlotContains():
            return True
else:
    ShapeTypeStrOrUnicode = ShapeTypeStr


if python_version >= 300:
    class ShapeTypeBytes(ShapeBase):
        @staticmethod
        def getTypeName():
            return "bytes"

        @staticmethod
        def hasShapeSlotLen():
            return True

        @staticmethod
        def hasShapeSlotInt():
            return False

        @staticmethod
        def hasShapeSlotLong():
            return False

        @staticmethod
        def hasShapeSlotFloat():
            return False

        @staticmethod
        def hasShapeSlotComplex():
            return False

        @staticmethod
        def hasShapeSlotIter():
            return True

        @staticmethod
        def hasShapeSlotNext():
            return False

        @staticmethod
        def getShapeIter():
            return ShapeTypeBytesIterator

        @staticmethod
        def hasShapeSlotContains():
            return True


    class ShapeTypeBytesIterator(ShapeIterator):
        @staticmethod
        def getTypeName():
            return "bytes_iterator"

        @staticmethod
        def hasShapeSlotLen():
            return False

else:
    ShapeTypeBytes = ShapeTypeStr
    ShapeTypeBytesIterator = ShapeTypeStrIterator


class ShapeTypeBytearray(ShapeBase):
    @staticmethod
    def getTypeName():
        return "bytearray"

    @staticmethod
    def hasShapeSlotLen():
        return True

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return True

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def getShapeIter():
        return ShapeTypeBytearrayIterator

    @staticmethod
    def hasShapeSlotContains():
        return True


class ShapeTypeBytearrayIterator(ShapeIterator):
    @staticmethod
    def getTypeName():
        return "bytearray_iterator"

    @staticmethod
    def hasShapeSlotLen():
        return False


class ShapeTypeEllipsisType(ShapeBase):
    @staticmethod
    def getTypeName():
        return "ellipsis"

    @staticmethod
    def hasShapeSlotLen():
        return False

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotContains():
        return True


class ShapeTypeSlice(ShapeBase):
    @staticmethod
    def getTypeName():
        return "slice"

    @staticmethod
    def hasShapeSlotLen():
        return False

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotContains():
        return False


class ShapeTypeXrange(ShapeBase):
    @staticmethod
    def getTypeName():
        return "xrange" if python_version < 300 else "range"

    @staticmethod
    def hasShapeSlotLen():
        return True

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return True

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def getShapeIter():
        return ShapeTypeXrangeIterator

    @staticmethod
    def hasShapeSlotContains():
        return True


class ShapeTypeXrangeIterator(ShapeIterator):
    @staticmethod
    def getTypeName():
        return "rangeiterator" if python_version < 300 else "range_iterator"

    @staticmethod
    def hasShapeSlotLen():
        return False


class ShapeTypeType(ShapeBase):
    @staticmethod
    def getTypeName():
        return "type"

    @staticmethod
    def hasShapeSlotLen():
        return False

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotContains():
        return False


class ShapeTypeModule(ShapeBase):
    @staticmethod
    def getTypeName():
        return "module"

    @staticmethod
    def hasShapeModule():
        return True

    @staticmethod
    def hasShapeSlotLen():
        return False

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotContains():
        return False


class ShapeTypeBuiltinModule(ShapeTypeModule):
    pass


class ShapeTypeFile(ShapeBase):
    @staticmethod
    def getTypeName():
        return "file"

    @staticmethod
    def hasShapeSlotLen():
        return False

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return True

    @staticmethod
    def hasShapeSlotNext():
        return True

    @staticmethod
    def hasShapeSlotContains():
        return True


class ShapeTypeStaticmethod(ShapeBase):
    @staticmethod
    def getTypeName():
        return "staticmethod"

    @staticmethod
    def hasShapeSlotLen():
        return False

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotContains():
        return False


class ShapeTypeClassmethod(ShapeBase):
    @staticmethod
    def getTypeName():
        return "classmethod"

    @staticmethod
    def hasShapeSlotLen():
        return False

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotContains():
        return False
