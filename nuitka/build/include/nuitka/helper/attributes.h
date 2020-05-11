//     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_HELPER_ATTRIBUTES_H__
#define __NUITKA_HELPER_ATTRIBUTES_H__

// Attribute lookup except special slots below.
extern PyObject *LOOKUP_ATTRIBUTE(PyObject *source, PyObject *attr_name);

// Attribute lookup of attribute slot "__dict__".
extern PyObject *LOOKUP_ATTRIBUTE_DICT_SLOT(PyObject *source);

// Attribute lookup of attribute slot "__class__".
extern PyObject *LOOKUP_ATTRIBUTE_CLASS_SLOT(PyObject *source);

// For built-in "hasattr" functionality.
extern int BUILTIN_HASATTR_BOOL(PyObject *source, PyObject *attr_name);

// Set an attribute except for attribute slots below.
extern bool SET_ATTRIBUTE(PyObject *target, PyObject *attr_name, PyObject *value);

// Set the "__dict__" special attribute slot.
extern bool SET_ATTRIBUTE_DICT_SLOT(PyObject *target, PyObject *value);

// Set the "__class__" special attribute slot.
extern bool SET_ATTRIBUTE_CLASS_SLOT(PyObject *target, PyObject *value);

// Special attribute lookups, e.g. "__enter__".
extern PyObject *LOOKUP_SPECIAL(PyObject *source, PyObject *attr_name);

// Find an attribute in a class, Python2 only.
#if PYTHON_VERSION < 300
extern PyObject *FIND_ATTRIBUTE_IN_CLASS(PyClassObject *klass, PyObject *attr_name);
#endif

#endif
