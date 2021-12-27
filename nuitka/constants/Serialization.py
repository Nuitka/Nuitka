#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Write and read constants data files and provide identifiers.

"""

import os
import pickle
import sys

from nuitka import OutputDirectories
from nuitka.__past__ import UnionType, basestring, to_byte, xrange
from nuitka.Builtins import (
    builtin_anon_codes,
    builtin_anon_values,
    builtin_exception_values_list,
)

# TODO: Move to constants
from nuitka.codegen.Namify import namifyConstant
from nuitka.containers.oset import OrderedSet
from nuitka.PythonVersions import python_version
from nuitka.utils.FileOperations import openTextFile


class BuiltinAnonValue(object):
    """Used to pickle anonymous values."""

    # Python3 values has no index, turn into a tuple.
    anon_values = tuple(builtin_anon_values.values())

    def __init__(self, anon_name):
        self.anon_name = anon_name

    def getStreamValueByte(self):
        """Return byte value, encoding the anon built-in value."""

        return to_byte(self.anon_values.index(self.anon_name))


class BuiltinUnionTypeValue(object):
    def __init__(self, args):
        self.args = args


class BuiltinSpecialValue(object):
    """Used to pickle special values."""

    def __init__(self, value):
        self.value = value

    def getStreamValueByte(self):
        """Return byte value, encoding the special built-in value."""

        # Currently the only one.
        if self.value == "Ellipsis":
            return to_byte(0)
        elif self.value == "NotImplemented":
            return to_byte(1)
        elif self.value == "Py_SysVersionInfo":
            return to_byte(2)
        else:
            assert False, self.value


class BlobData(object):
    """Used to pickle bytes to become raw pointers."""

    def __init__(self, data):
        self.data = data

    def getData(self):
        return self.data


def _pickleAnonValues(pickler, value):
    if value in builtin_anon_values:
        pickler.save(BuiltinAnonValue(builtin_anon_values[value]))
    elif value is Ellipsis:
        pickler.save(BuiltinSpecialValue("Ellipsis"))
    elif value is NotImplemented:
        pickler.save(BuiltinSpecialValue("NotImplemented"))
    elif value is sys.version_info:
        pickler.save(BuiltinSpecialValue("Py_SysVersionInfo"))
    else:
        pickler.save_global(value)


def _pickeUnionType(picker, value):
    picker.save(BuiltinUnionTypeValue(value.__args__))


class ConstantStreamWriter(object):
    """Write constants to a stream and return numbers for them."""

    def __init__(self, filename):
        self.count = 0

        filename = os.path.join(OutputDirectories.getSourceDirectoryPath(), filename)
        self.file = openTextFile(filename, "wb")
        if python_version < 0x300:
            self.pickle = pickle.Pickler(self.file, -1)
        else:
            self.pickle = pickle._Pickler(  # pylint: disable=I0021,protected-access
                self.file, -1
            )

        self.pickle.dispatch[type] = _pickleAnonValues
        self.pickle.dispatch[type(Ellipsis)] = _pickleAnonValues
        self.pickle.dispatch[type(NotImplemented)] = _pickleAnonValues

        if type(sys.version_info) is not tuple:
            self.pickle.dispatch[type(sys.version_info)] = _pickleAnonValues

        # Standard pickling doesn't work with our necessary wrappers.
        if python_version >= 0x3A0:
            self.pickle.dispatch[UnionType] = _pickeUnionType

    def addConstantValue(self, constant_value):
        self.pickle.dump(constant_value)
        self.count += 1

    def addBlobData(self, data):
        self.pickle.dump(BlobData(data))
        self.count += 1

    def close(self):
        self.file.close()


class ConstantStreamReader(object):
    def __init__(self, const_file):
        self.count = 0
        self.pickle = pickle.Unpickler(const_file)

    def readConstantValue(self):
        return self.pickle.load()


class ConstantAccessor(object):
    def __init__(self, data_filename, top_level_name):
        self.constants = OrderedSet()

        self.constants_writer = ConstantStreamWriter(data_filename)
        self.top_level_name = top_level_name

    def getConstantCode(self, constant):
        # Use in user code, or for constants building code itself, many
        # constant types get special code immediately.
        # pylint: disable=too-many-branches,too-many-statements
        if constant is None:
            key = "Py_None"
        elif constant is True:
            key = "Py_True"
        elif constant is False:
            key = "Py_False"
        elif constant is Ellipsis:
            key = "Py_Ellipsis"
        elif constant is NotImplemented:
            key = "Py_NotImplemented"
        elif constant is sys.version_info:
            key = "Py_SysVersionInfo"
        elif type(constant) is type:
            # TODO: Maybe make this a mapping in nuitka.Builtins

            if constant is None:
                key = "(PyObject *)Py_TYPE(Py_None)"
            elif constant is object:
                key = "(PyObject *)&PyBaseObject_Type"
            elif constant is staticmethod:
                key = "(PyObject *)&PyStaticMethod_Type"
            elif constant is classmethod:
                key = "(PyObject *)&PyClassMethod_Type"
            elif constant is bytearray:
                key = "(PyObject *)&PyByteArray_Type"
            elif constant is enumerate:
                key = "(PyObject *)&PyEnum_Type"
            elif constant is frozenset:
                key = "(PyObject *)&PyFrozenSet_Type"
            elif python_version >= 0x270 and constant is memoryview:
                key = "(PyObject *)&PyMemoryView_Type"
            elif python_version < 0x300 and constant is basestring:
                key = "(PyObject *)&PyBaseString_Type"
            elif python_version < 0x300 and constant is xrange:
                key = "(PyObject *)&PyRange_Type"
            elif constant in builtin_anon_values:
                key = "(PyObject *)" + builtin_anon_codes[builtin_anon_values[constant]]
            elif constant in builtin_exception_values_list:
                key = "(PyObject *)PyExc_%s" % constant.__name__
            else:
                type_name = constant.__name__

                if constant is int and python_version >= 0x300:
                    type_name = "long"
                elif constant is str:
                    type_name = "string" if python_version < 0x300 else "unicode"

                key = "(PyObject *)&Py%s_Type" % type_name.capitalize()
        else:
            key = "const_" + namifyConstant(constant)

            if key not in self.constants:
                self.constants.add(key)
                self.constants_writer.addConstantValue(constant)

            key = "%s[%d]" % (self.top_level_name, self.constants.index(key))

        # TODO: Make it returning, more clear.
        return key

    def getBlobDataCode(self, data):
        key = "blob_" + namifyConstant(data)

        if key not in self.constants:
            self.constants.add(key)
            self.constants_writer.addBlobData(data)

        key = "%s[%d]" % (self.top_level_name, self.constants.index(key))

        return key

    def getConstantsCount(self):
        # Make sure to add no more after asking this.
        self.constants_writer.close()

        return len(self.constants)
