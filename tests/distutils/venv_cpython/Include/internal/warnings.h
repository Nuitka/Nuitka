#ifndef Py_INTERNAL_WARNINGS_H
#define Py_INTERNAL_WARNINGS_H
#ifdef __cplusplus
extern "C" {
#endif

#include "object.h"

struct _warnings_runtime_state {
    /* Both 'filters' and 'onceregistry' can be set in warnings.py;
       get_warnings_attr() will reset these variables accordingly. */
    PyObject *filters;  /* List */
    PyObject *once_registry;  /* Dict */
    PyObject *default_action; /* String */
    long filters_version;
};

#ifdef __cplusplus
}
#endif
#endif /* !Py_INTERNAL_WARNINGS_H */
