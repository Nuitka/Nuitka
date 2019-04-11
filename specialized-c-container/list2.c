#include <Python.h>
#include "NuitkaAPI.c"


static PyObject *list2(PyObject* self, PyObject* args)
{
	int i = 0;
	PyObject *a = Py_BuildValue("i", 7);
	PyObject *result = NuitkaList_New(1);
	NuitkaList_SetItem(result, 0, a);

	for(i = 0;i<7; i++)
	{
		NuitkaList_Append(result,a);
	}


	return NuitkaList_Sum(result);
}


static PyMethodDef myMethods[] = {
    { "list2", list2, METH_NOARGS, "list sum" },
    { NULL, NULL, 0, NULL }
};

// Our Module Definition struct
static struct PyModuleDef NuitkaListModule = {
    PyModuleDef_HEAD_INIT,
    "NuitkaListModule",
    "Test Module",
    -1,
    myMethods
};

// Initializes our module using our above struct
PyMODINIT_FUNC PyInit_NuitkaListModule(void)
{
    return PyModule_Create(&NuitkaListModule);
}

