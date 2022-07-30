//     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
//
//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     Licensed under the Apache License, Version 2.0 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        http://www.apache.org/licenses/LICENSE-2.0
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
//
/* WARNING, this code is GENERATED. Modify the template HelperOperationBinary.c.j2 instead! */

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

/* C helpers for type specialized "+" (ADD) operations */

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_INT_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_OBJECT_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_INT_OBJECT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
extern nuitka_bool BINARY_OPERATION_ADD_NBOOL_INT_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
extern nuitka_bool BINARY_OPERATION_ADD_NBOOL_OBJECT_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
extern nuitka_bool BINARY_OPERATION_ADD_NBOOL_INT_OBJECT(PyObject *operand1, PyObject *operand2);
#endif

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LONG" to Python2 'long', Python3 'int'. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_LONG_LONG(PyObject *operand1, PyObject *operand2);

/* Code referring to "OBJECT" corresponds to any Python object and "LONG" to Python2 'long', Python3 'int'. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_OBJECT_LONG(PyObject *operand1, PyObject *operand2);

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "OBJECT" to any Python object. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_LONG_OBJECT(PyObject *operand1, PyObject *operand2);

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LONG" to Python2 'long', Python3 'int'. */
extern nuitka_bool BINARY_OPERATION_ADD_NBOOL_LONG_LONG(PyObject *operand1, PyObject *operand2);

/* Code referring to "OBJECT" corresponds to any Python object and "LONG" to Python2 'long', Python3 'int'. */
extern nuitka_bool BINARY_OPERATION_ADD_NBOOL_OBJECT_LONG(PyObject *operand1, PyObject *operand2);

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "OBJECT" to any Python object. */
extern nuitka_bool BINARY_OPERATION_ADD_NBOOL_LONG_OBJECT(PyObject *operand1, PyObject *operand2);

/* Code referring to "FLOAT" corresponds to Python 'float' and "FLOAT" to Python 'float'. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2);

/* Code referring to "OBJECT" corresponds to any Python object and "FLOAT" to Python 'float'. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2);

/* Code referring to "FLOAT" corresponds to Python 'float' and "OBJECT" to any Python object. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2);

/* Code referring to "FLOAT" corresponds to Python 'float' and "FLOAT" to Python 'float'. */
extern nuitka_bool BINARY_OPERATION_ADD_NBOOL_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2);

/* Code referring to "OBJECT" corresponds to any Python object and "FLOAT" to Python 'float'. */
extern nuitka_bool BINARY_OPERATION_ADD_NBOOL_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2);

/* Code referring to "FLOAT" corresponds to Python 'float' and "OBJECT" to any Python object. */
extern nuitka_bool BINARY_OPERATION_ADD_NBOOL_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2);

/* Code referring to "FLOAT" corresponds to Python 'float' and "LONG" to Python2 'long', Python3 'int'. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_FLOAT_LONG(PyObject *operand1, PyObject *operand2);

/* Code referring to "FLOAT" corresponds to Python 'float' and "LONG" to Python2 'long', Python3 'int'. */
extern nuitka_bool BINARY_OPERATION_ADD_NBOOL_FLOAT_LONG(PyObject *operand1, PyObject *operand2);

#if PYTHON_VERSION < 0x300
/* Code referring to "FLOAT" corresponds to Python 'float' and "INT" to Python2 'int'. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_FLOAT_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "FLOAT" corresponds to Python 'float' and "INT" to Python2 'int'. */
extern nuitka_bool BINARY_OPERATION_ADD_NBOOL_FLOAT_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "INT" to Python2 'int'. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_LONG_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "INT" to Python2 'int'. */
extern nuitka_bool BINARY_OPERATION_ADD_NBOOL_LONG_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "CLONG" to C platform long value. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_INT_CLONG(PyObject *operand1, long operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "CLONG" to C platform long value. */
extern nuitka_bool BINARY_OPERATION_ADD_NBOOL_INT_CLONG(PyObject *operand1, long operand2);
#endif

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "DIGIT" to C platform digit value for long
 * Python objects. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_LONG_DIGIT(PyObject *operand1, long operand2);

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "DIGIT" to C platform digit value for long
 * Python objects. */
extern nuitka_bool BINARY_OPERATION_ADD_NBOOL_LONG_DIGIT(PyObject *operand1, long operand2);

/* Code referring to "FLOAT" corresponds to Python 'float' and "CFLOAT" to C platform float value. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_FLOAT_CFLOAT(PyObject *operand1, double operand2);

/* Code referring to "FLOAT" corresponds to Python 'float' and "CFLOAT" to C platform float value. */
extern nuitka_bool BINARY_OPERATION_ADD_NBOOL_FLOAT_CFLOAT(PyObject *operand1, double operand2);

#if PYTHON_VERSION < 0x300
/* Code referring to "STR" corresponds to Python2 'str' and "STR" to Python2 'str'. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_STR_STR(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "STR" to Python2 'str'. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_OBJECT_STR(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "STR" corresponds to Python2 'str' and "OBJECT" to any Python object. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_STR_OBJECT(PyObject *operand1, PyObject *operand2);
#endif

/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "UNICODE" to Python2 'unicode',
 * Python3 'str'. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_UNICODE_UNICODE(PyObject *operand1, PyObject *operand2);

/* Code referring to "OBJECT" corresponds to any Python object and "UNICODE" to Python2 'unicode', Python3 'str'. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_OBJECT_UNICODE(PyObject *operand1, PyObject *operand2);

/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "OBJECT" to any Python object. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_UNICODE_OBJECT(PyObject *operand1, PyObject *operand2);

#if PYTHON_VERSION >= 0x300
/* Code referring to "BYTES" corresponds to Python3 'bytes' and "BYTES" to Python3 'bytes'. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_BYTES_BYTES(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION >= 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "BYTES" to Python3 'bytes'. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_OBJECT_BYTES(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION >= 0x300
/* Code referring to "BYTES" corresponds to Python3 'bytes' and "OBJECT" to any Python object. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_BYTES_OBJECT(PyObject *operand1, PyObject *operand2);
#endif

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "TUPLE" to Python 'tuple'. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_TUPLE_TUPLE(PyObject *operand1, PyObject *operand2);

/* Code referring to "OBJECT" corresponds to any Python object and "TUPLE" to Python 'tuple'. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_OBJECT_TUPLE(PyObject *operand1, PyObject *operand2);

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "OBJECT" to any Python object. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_TUPLE_OBJECT(PyObject *operand1, PyObject *operand2);

/* Code referring to "LIST" corresponds to Python 'list' and "LIST" to Python 'list'. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_LIST_LIST(PyObject *operand1, PyObject *operand2);

/* Code referring to "OBJECT" corresponds to any Python object and "LIST" to Python 'list'. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_OBJECT_LIST(PyObject *operand1, PyObject *operand2);

/* Code referring to "LIST" corresponds to Python 'list' and "OBJECT" to any Python object. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_LIST_OBJECT(PyObject *operand1, PyObject *operand2);

/* Code referring to "LIST" corresponds to Python 'list' and "LIST" to Python 'list'. */
extern nuitka_bool BINARY_OPERATION_ADD_NBOOL_LIST_LIST(PyObject *operand1, PyObject *operand2);

/* Code referring to "OBJECT" corresponds to any Python object and "LIST" to Python 'list'. */
extern nuitka_bool BINARY_OPERATION_ADD_NBOOL_OBJECT_LIST(PyObject *operand1, PyObject *operand2);

/* Code referring to "LIST" corresponds to Python 'list' and "OBJECT" to any Python object. */
extern nuitka_bool BINARY_OPERATION_ADD_NBOOL_LIST_OBJECT(PyObject *operand1, PyObject *operand2);

#if PYTHON_VERSION < 0x300
/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "STR" to Python2 'str'. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_UNICODE_STR(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "STR" corresponds to Python2 'str' and "UNICODE" to Python2 'unicode', Python3 'str'. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_STR_UNICODE(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "STR" to Python2 'str'. */
extern nuitka_bool BINARY_OPERATION_ADD_NBOOL_UNICODE_STR(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "STR" corresponds to Python2 'str' and "UNICODE" to Python2 'unicode', Python3 'str'. */
extern nuitka_bool BINARY_OPERATION_ADD_NBOOL_STR_UNICODE(PyObject *operand1, PyObject *operand2);
#endif

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
extern PyObject *BINARY_OPERATION_ADD_OBJECT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2);

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
extern nuitka_bool BINARY_OPERATION_ADD_NBOOL_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2);
