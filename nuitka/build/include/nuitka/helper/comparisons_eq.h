//     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
/* WARNING, this code is GENERATED. Modify the template HelperOperationComparison.c.j2 instead! */

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

/* C helpers for type specialized "==" (EQ) comparisons */

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
extern PyObject *RICH_COMPARE_EQ_OBJECT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2);

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
extern bool RICH_COMPARE_EQ_CBOOL_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2);

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
extern nuitka_bool RICH_COMPARE_EQ_NBOOL_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2);

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "STR" to Python2 'str'. */
extern PyObject *RICH_COMPARE_EQ_OBJECT_OBJECT_STR(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "STR" to Python2 'str'. */
extern bool RICH_COMPARE_EQ_CBOOL_OBJECT_STR(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "STR" to Python2 'str'. */
extern nuitka_bool RICH_COMPARE_EQ_NBOOL_OBJECT_STR(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "STR" corresponds to Python2 'str' and "OBJECT" to any Python object. */
extern PyObject *RICH_COMPARE_EQ_OBJECT_STR_OBJECT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "STR" corresponds to Python2 'str' and "OBJECT" to any Python object. */
extern bool RICH_COMPARE_EQ_CBOOL_STR_OBJECT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "STR" corresponds to Python2 'str' and "OBJECT" to any Python object. */
extern nuitka_bool RICH_COMPARE_EQ_NBOOL_STR_OBJECT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
extern PyObject *RICH_COMPARE_EQ_OBJECT_INT_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
extern bool RICH_COMPARE_EQ_CBOOL_INT_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
extern nuitka_bool RICH_COMPARE_EQ_NBOOL_INT_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
extern PyObject *RICH_COMPARE_EQ_OBJECT_OBJECT_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
extern bool RICH_COMPARE_EQ_CBOOL_OBJECT_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
extern nuitka_bool RICH_COMPARE_EQ_NBOOL_OBJECT_INT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
extern PyObject *RICH_COMPARE_EQ_OBJECT_INT_OBJECT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
extern bool RICH_COMPARE_EQ_CBOOL_INT_OBJECT(PyObject *operand1, PyObject *operand2);
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
extern nuitka_bool RICH_COMPARE_EQ_NBOOL_INT_OBJECT(PyObject *operand1, PyObject *operand2);
#endif

/* Code referring to "FLOAT" corresponds to Python 'float' and "FLOAT" to Python 'float'. */
extern PyObject *RICH_COMPARE_EQ_OBJECT_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2);

/* Code referring to "FLOAT" corresponds to Python 'float' and "FLOAT" to Python 'float'. */
extern bool RICH_COMPARE_EQ_CBOOL_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2);

/* Code referring to "FLOAT" corresponds to Python 'float' and "FLOAT" to Python 'float'. */
extern nuitka_bool RICH_COMPARE_EQ_NBOOL_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2);

/* Code referring to "OBJECT" corresponds to any Python object and "FLOAT" to Python 'float'. */
extern PyObject *RICH_COMPARE_EQ_OBJECT_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2);

/* Code referring to "OBJECT" corresponds to any Python object and "FLOAT" to Python 'float'. */
extern bool RICH_COMPARE_EQ_CBOOL_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2);

/* Code referring to "OBJECT" corresponds to any Python object and "FLOAT" to Python 'float'. */
extern nuitka_bool RICH_COMPARE_EQ_NBOOL_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2);

/* Code referring to "FLOAT" corresponds to Python 'float' and "OBJECT" to any Python object. */
extern PyObject *RICH_COMPARE_EQ_OBJECT_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2);

/* Code referring to "FLOAT" corresponds to Python 'float' and "OBJECT" to any Python object. */
extern bool RICH_COMPARE_EQ_CBOOL_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2);

/* Code referring to "FLOAT" corresponds to Python 'float' and "OBJECT" to any Python object. */
extern nuitka_bool RICH_COMPARE_EQ_NBOOL_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2);

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "TUPLE" to Python 'tuple'. */
extern PyObject *RICH_COMPARE_EQ_OBJECT_TUPLE_TUPLE(PyObject *operand1, PyObject *operand2);

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "TUPLE" to Python 'tuple'. */
extern bool RICH_COMPARE_EQ_CBOOL_TUPLE_TUPLE(PyObject *operand1, PyObject *operand2);

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "TUPLE" to Python 'tuple'. */
extern nuitka_bool RICH_COMPARE_EQ_NBOOL_TUPLE_TUPLE(PyObject *operand1, PyObject *operand2);

/* Code referring to "OBJECT" corresponds to any Python object and "TUPLE" to Python 'tuple'. */
extern PyObject *RICH_COMPARE_EQ_OBJECT_OBJECT_TUPLE(PyObject *operand1, PyObject *operand2);

/* Code referring to "OBJECT" corresponds to any Python object and "TUPLE" to Python 'tuple'. */
extern bool RICH_COMPARE_EQ_CBOOL_OBJECT_TUPLE(PyObject *operand1, PyObject *operand2);

/* Code referring to "OBJECT" corresponds to any Python object and "TUPLE" to Python 'tuple'. */
extern nuitka_bool RICH_COMPARE_EQ_NBOOL_OBJECT_TUPLE(PyObject *operand1, PyObject *operand2);

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "OBJECT" to any Python object. */
extern PyObject *RICH_COMPARE_EQ_OBJECT_TUPLE_OBJECT(PyObject *operand1, PyObject *operand2);

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "OBJECT" to any Python object. */
extern bool RICH_COMPARE_EQ_CBOOL_TUPLE_OBJECT(PyObject *operand1, PyObject *operand2);

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "OBJECT" to any Python object. */
extern nuitka_bool RICH_COMPARE_EQ_NBOOL_TUPLE_OBJECT(PyObject *operand1, PyObject *operand2);
