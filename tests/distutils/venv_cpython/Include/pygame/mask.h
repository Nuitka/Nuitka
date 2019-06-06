#include <Python.h>
#include "bitmask.h"

#define PYGAMEAPI_MASK_FIRSTSLOT 0
#define PYGAMEAPI_MASK_NUMSLOTS 1
#define PYGAMEAPI_LOCAL_ENTRY "_PYGAME_C_API"

typedef struct {
  PyObject_HEAD
  bitmask_t *mask;
} PyMaskObject;

#define PyMask_AsBitmap(x) (((PyMaskObject*)x)->mask)

#ifndef PYGAMEAPI_MASK_INTERNAL

#define PyMask_Type     (*(PyTypeObject*)PyMASK_C_API[0])
#define PyMask_Check(x) ((x)->ob_type == &PyMask_Type)

#define import_pygame_mask() \
    _IMPORT_PYGAME_MODULE(mask, MASK, PyMASK_C_API)

static void* PyMASK_C_API[PYGAMEAPI_MASK_NUMSLOTS] = {NULL};
#endif /* #ifndef PYGAMEAPI_MASK_INTERNAL */

