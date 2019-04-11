#include <Python.h>

PyObject *globalBuffer[100];

static size_t idx = 0;
//make a new list
static PyObject *NuitkaList_New(size_t n)
{
	idx = n;
	return Py_None;
}

static PyObject *NuitkaList_SetItem(PyObject *list,size_t i,PyObject *item)
{
	globalBuffer[i] = PyLong_AsLong(item); 
	return Py_None;

}

static PyObject *NuitkaList_Append(PyObject *list,PyObject *item)
{
	globalBuffer[idx] = item;

	idx = idx+ 1;
	return Py_None;
}
static PyObject *NuitkaList_Sum(PyObject *list)
{
	int sum = 0;
	int i = 0;
	for(; i <7;i++)
	{
		sum = sum + globalBuffer[i];
	}
	return Py_BuildValue("i", sum);

}
