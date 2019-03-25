#include <Python.h>

static PyObject* GetList(PyObject* self, PyObject* args)
{
    srand(time(NULL));
    int const n = 10;
    int element = 10;
    PyObject* python_val = PyList_New(n);
    for (int i = 0; i < n; ++i)
    {
        int r = rand() % 10;
        PyObject* python_int = Py_BuildValue("i", r);
        PyList_SetItem(python_val, i, python_int);
    }
    PyList_Append(python_val, PyFloat_FromDouble(element)); 
    PyList_Append(python_val, PyFloat_FromDouble(element)); 
    PyList_Append(python_val, PyFloat_FromDouble(element)); 
    return python_val;
}

static PyMethodDef myMethods[] = {
    { "GetList", GetList, METH_NOARGS, "Return List" },
    { NULL, NULL, 0, NULL }
};

static struct PyModuleDef myModule = {
    PyModuleDef_HEAD_INIT,
    "myModule",
    "Test Module",
    -1,
    myMethods
};
PyMODINIT_FUNC PyInit_myModule(void)
{
    return PyModule_Create(&myModule);
}