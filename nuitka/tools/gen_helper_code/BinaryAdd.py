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
#include<stdio.h>
#include<ctype.h>
#include <string.h>

int sum_int(int operand1, int operand2)
{
	int i = 0, a, b;
	a = operand1;
	b = operand2;

	// adding both Integer operands
	i = a + b;

	return (i);
}

float sum_float(float operand1, float operand2)
{
	float i = 0.0, a, b;
	a = operand1;
	b = operand2;

	// adding both Float operands
	i = a + b;

	return (i);
}

int toInteger(char a[]) {
	int c, sign, offset, n;
	
	if (a[0] == '-') {  // Handle negative integers
		sign = -1;
	}
	if (sign == -1) {  // Set starting position to convert
		offset = 1;
	}
	else {
		offset = 0;
	}
	
	n = 0;

	for (c = offset; a[c] != '\0'; c++) {
		n = n * 10 + a[c] - '0';
	}
	if (sign == -1) {
		n = -n;
	}
	return n;
}

float ToFloat(char *string)
{
		float result = 0.0;
		int len = strlen(string);
		int dotPosition = 0;

		for (int i = 0; i < len; i++)
		{
				if (string[i] == '.')
				{
					dotPosition = len - i  - 1;
				}
				else
				{
					result = result * 10.0 + (string[i]-'0');
				}
			}

			while (dotPosition--)
			{
				result /= 10.0;
			}

		return result;
}

int main(int args, char* argv[])
{
	// Values passed from python in the form of char array
	int a, b, int_add = 0, t;
	float float_add = 0.0, m, n;

	t = toInteger(argv[3]);

	if(t == 1){

		// Conversion from string to Integer
		a = toInteger(argv[1]);
		b = toInteger(argv[2]);

		int_add = sum_int(a, b);
		printf("Sum of Two Number is : %d\n", int_add);
		return int_add;
	}
	else {

		// Conversion from string to Float
		m = ToFloat(argv[1]);
		n = ToFloat(argv[2]);

		float_add = sum_float(m, n);
		printf("Sum of Two Number is : %f\n", float_add);
		return float_add;
	}
	return 0;
}
"""

# Jinja Template 
# Value of Operands are passed from Jinja2 to Python code
addtemp = Template("Add operand1 + operand2 = {{ add(operand1 = 2, operand2 = 4) }}")

# Template is rendered and returned output is stored and displayed
addition = addtemp.render(add=add)
print(addition)
