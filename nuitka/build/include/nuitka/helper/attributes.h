//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#ifndef __NUITKA_HELPER_ATTRIBUTES_H__
#define __NUITKA_HELPER_ATTRIBUTES_H__

// Attribute lookup except special slots below.
extern PyObject *LOOKUP_ATTRIBUTE(PyThreadState *tstate, PyObject *source, PyObject *attr_name);

// Attribute lookup of attribute slot "__dict__".
extern PyObject *LOOKUP_ATTRIBUTE_DICT_SLOT(PyThreadState *tstate, PyObject *source);

// Attribute lookup of attribute slot "__class__".
extern PyObject *LOOKUP_ATTRIBUTE_CLASS_SLOT(PyThreadState *tstate, PyObject *source);

// For built-in "hasattr" functionality.
extern int BUILTIN_HASATTR_BOOL(PyThreadState *tstate, PyObject *source, PyObject *attr_name);

// Check for an attribute, cannot raise an exception.
extern bool HAS_ATTR_BOOL(PyThreadState *tstate, PyObject *source, PyObject *attr_name);

// Check for an attribute, can raise an exception.
extern int HAS_ATTR_BOOL2(PyThreadState *tstate, PyObject *source, PyObject *attr_name);

// Set an attribute except for attribute slots below.
extern bool SET_ATTRIBUTE(PyThreadState *tstate, PyObject *target, PyObject *attr_name, PyObject *value);

// Set the "__dict__" special attribute slot.
extern bool SET_ATTRIBUTE_DICT_SLOT(PyThreadState *tstate, PyObject *target, PyObject *value);

// Set the "__class__" special attribute slot.
extern bool SET_ATTRIBUTE_CLASS_SLOT(PyThreadState *tstate, PyObject *target, PyObject *value);

// Special attribute lookups, e.g. "__enter__".
extern PyObject *LOOKUP_SPECIAL(PyThreadState *tstate, PyObject *source, PyObject *attr_name);

// Find an attribute in a class, Python2 only.
#if PYTHON_VERSION < 0x300
extern PyObject *FIND_ATTRIBUTE_IN_CLASS(PyClassObject *class_object, PyObject *attr_name);
#endif

extern PyObject *LOOKUP_MODULE_VALUE(PyDictObject *module_dict, PyObject *var_name);

// In case of DLL usage, this avoids looking up the symbol from it.
extern getattrofunc PyObject_GenericGetAttr_resolved;

// Avoid repeated code, this checks if a type has the standard implementation, then
// we can just try and do the same in slightly faster ways.
static inline bool hasTypeGenericGetAttr(PyTypeObject *type) {
#if PYTHON_VERSION >= 0x3b0
    // TODO: Big performance loss here
    return false;
#else
    return type->tp_getattro == PyObject_GenericGetAttr_resolved;
#endif
}

// In case of DLL usage, this avoids looking up the symbol from it.
extern setattrofunc PyObject_GenericSetAttr_resolved;

static inline bool hasTypeGenericSetAttr(PyTypeObject *type) {
#if PYTHON_VERSION >= 0x3b0
    // TODO: Big performance loss here
    return false;
#else
    return type->tp_setattro == PyObject_GenericSetAttr_resolved;
#endif
}

#if PYTHON_VERSION >= 0x3a0
static inline bool Nuitka_Descr_IsData(PyObject *object) { return Py_TYPE(object)->tp_descr_set != NULL; }
#else
#define Nuitka_Descr_IsData(object) PyDescr_IsData(object)
#endif

// ---------------------------------------------------------------------------
// Per-call-site version-tag inline cache for Python 3.13+ GIL builds.
//
// Codegen emits one static NitroAttrCache per LOOKUP_ATTRIBUTE call site.
// On the hot path (type version tag matches) the cache delivers the attribute
// with a single bounds-checked array load — no hash probing, no C-API calls.
//
// Cache state encoding (type_ver field):
//   0            → not yet filled (C zero-initialises static-storage objects)
//   0xFFFFFFFF   → tried but not cacheable (descriptor, combined dict, etc.)
//   otherwise    → valid entry; must equal Py_TYPE(obj)->tp_version_tag to hit
//
// Byte layout of PyDictValues on Python 3.13+ 64-bit GIL builds:
//   [0] capacity  u8      — total allocated value slots
//   [1] nused     u8      — used slots (attributes assigned so far)
//   [2] prefix_size u8
//   [3..7] padding        — alignment to 8 bytes
//   [8..] PyObject *values[]
// ---------------------------------------------------------------------------
#if PYTHON_VERSION >= 0x3d0

typedef struct {
    uint32_t type_ver;
    int32_t offset; // >= 0: byte offset from obj base to PyObject* slot in inline values
} NitroAttrCache;

#define NITRO_DICT_VALUES_HEADER_SIZE 8

// Hot path: returns a new reference on cache hit, NULL on miss or first call.
// On a stale version-tag mismatch resets type_ver to 0 for re-fill on next call.
static inline PyObject *Nuitka_Nitro_CachedGetAttr(PyObject *obj, NitroAttrCache *cache) {
    uint32_t ver = cache->type_ver;
    if (ver == 0 || ver == 0xFFFFFFFFu)
        return NULL;

    PyTypeObject *tp = Py_TYPE(obj);
    if (ver != tp->tp_version_tag) {
        cache->type_ver = 0; // stale — trigger refill on next miss
        return NULL;
    }

    int32_t off = cache->offset;
    if (off < 0)
        return NULL; // type known not to use inline values

    PyObject *val = *(PyObject **)((char *)obj + (uint32_t)off);
    if (val == NULL)
        return NULL; // slot empty for this instance (attribute not set)

    Py_INCREF(val);
    return val;
}

// Slow path: fills *cache from the object's inline values layout.
// Called only after a miss when cache->type_ver == 0.
extern void Nuitka_Nitro_CacheFill(PyObject *obj, PyObject *attr_val, NitroAttrCache *cache);

#endif /* PYTHON_VERSION >= 0x3d0 */

#endif

//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     Licensed under the GNU Affero General Public License, Version 3 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        http://www.gnu.org/licenses/agpl.txt
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
