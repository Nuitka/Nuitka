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
// Per-call-site version-tag inline cache for Python 3.12+ builds.
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
// Byte layout of PyDictValues (both 3.12 and 3.13):
//   [0] capacity  u8      — total allocated value slots
//   [1..sizeof(void*)-1]  — alignment padding
//   [sizeof(void*)..]     — PyObject *values[]
//
// Pre-header layout differs by version (all offsets from obj pointer):
//   3.12 GIL:        obj-16 = PyObject* dict (NULL if inline), obj-8 = PyDictValues* vals
//   3.13+ GIL:       obj-24 = PyObject* dict (NULL if inline)
//   3.13+ no-GIL:    obj-16 = PyObject* dict (NULL if inline)
// ---------------------------------------------------------------------------
#if PYTHON_VERSION >= 0x3c0 && !defined(Py_GIL_DISABLED)

typedef struct {
    uint32_t type_ver;
    int32_t offset; // >= 0: byte offset from obj base to PyObject* slot in inline values
} NitroAttrCache;

#define NITRO_DICT_VALUES_HEADER_SIZE ((int)sizeof(void *))

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
        return NULL;

#if PYTHON_VERSION >= 0x3d0
    // 3.13+: dictionary pointer is in the pre-header. If it's non-NULL, the
    // instance has transitioned to a combined dictionary and inline values
    // are no longer valid.
    if (*(PyObject **)((char *)obj - 3 * sizeof(PyObject *)) != NULL)
        return NULL;
#else
    // 3.12: when an instance transitions from inline to combined dict the values
    // pointer at obj-8 is set to NULL but the inline buffer is NOT cleared.
    // We must verify the instance is still using inline values before reading.
    if (*(void **)((char *)obj - sizeof(void *)) != (void *)((char *)obj + tp->tp_basicsize))
        return NULL;
#endif

    PyObject *val = *(PyObject **)((char *)obj + (uint32_t)off);
    if (val == NULL)
        return NULL; // slot empty for this instance (attribute not set)

    Py_INCREF(val);
    return val;
}

// Hot path for hasattr: returns 1 (found), 0 (not found), -1 (cache miss or uncacheable).
// Bypasses INCREF/DECREF and exception handling.
static inline int Nuitka_Nitro_CachedHasAttr(PyObject *obj, NitroAttrCache *cache) {
    uint32_t ver = cache->type_ver;
    if (ver == 0 || ver == 0xFFFFFFFFu)
        return -1;

    PyTypeObject *tp = Py_TYPE(obj);
    if (ver != tp->tp_version_tag) {
        cache->type_ver = 0; // stale
        return -1;
    }

    int32_t off = cache->offset;
    if (off < 0)
        return -1;

#if PYTHON_VERSION >= 0x3d0
    if (*(PyObject **)((char *)obj - 3 * sizeof(PyObject *)) != NULL)
        return -1;
#else
    if (*(void **)((char *)obj - sizeof(void *)) != (void *)((char *)obj + tp->tp_basicsize))
        return -1;
#endif

    return (*(PyObject **)((char *)obj + (uint32_t)off) != NULL) ? 1 : 0;
}

// Slow path: fills *cache from the object's inline values layout.
// Called only after a miss when cache->type_ver == 0.
extern void Nuitka_Nitro_CacheFill(PyObject *obj, PyObject *attr_val, NitroAttrCache *cache);

#endif /* PYTHON_VERSION >= 0x3c0 && !defined(Py_GIL_DISABLED) */

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
