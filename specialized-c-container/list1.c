#include <Python.h>
//this is the list implementation with python c api
static PyObject *list1(PyObject* self, PyObject* args)
{	

	int i = 0;
	PyObject *a = Py_BuildValue("i", 7);
	PyObject *result = PyList_New(1);
	PyList_SetItem(result, 0, a);

	
	for(;i<7; i++)
	{
		PyList_Append(result,a);
	}

	return result;
}

static PyMethodDef myMethods[] = {
    { "list1", list1, METH_NOARGS, "make a list" },
    { NULL, NULL, 0, NULL }
};

// Our Module Definition struct
static struct PyModuleDef myModule = {
    PyModuleDef_HEAD_INIT,
    "myModule",
    "Test Module",
    -1,
    myMethods
};

// Initializes our module using our above struct
PyMODINIT_FUNC PyInit_myModule(void)
{
    return PyModule_Create(&myModule);
}


