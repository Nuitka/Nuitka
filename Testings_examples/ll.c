import subprocess
import os
from jinja2 import Template


def isType(op1, op2):
  # Operands are compared and checked for their type and value is returned
  # It checks for operand to be int, float or object
  if type(op1) == int:
    if type(op2) == int:
      return 1
  elif type(op1) == float:
    if type(op2) == float:
      return 0
  else:
    return "PyInt_Check(%s)" % op1


def add(operand1, operand2):
  # operands are passed for data type check to isType()
  operand_type = isType(operand1, operand2)
  a = str(operand1)
  b = str(operand2)
  t = str(operand_type)

  # Subprocess call is used to run C code with passed values 
  if not os.path.exists('binary_add'):
    f = open('binary_add.c', 'w')
    f.write(prog)
    f.close()
    subprocess.call(["gcc", "binary_add.c"])
  temp = subprocess.call(["./a.out", a, b, t])
  # Summed-up values recieved from C code are printed and then returned to jinja2
  print("Sum of two operands is : ", temp)
  return temp


prog = r"""
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
"""

# Jinja Template 
# Value of Operands are passed from Jinja2 to Python code
addtemp = Template("Add operand1 + operand2 = {{ add(operand1 = 2, operand2 = 4) }}")

# Template is rendered and returned output is stored and displayed
addition = addtemp.render(add=add)
print(addition)



