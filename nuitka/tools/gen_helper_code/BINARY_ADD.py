from jinja2 import Template

def add(a, b):
	if(isinstance(a,str)):
		if(isinstance(b,str)):
			c = a+b
			return c
		print("Not an integer")
	else:
		if (type(int(a)))==int:
			if(isinstance(a,float)):
				print("Not an Integer")
			else:
				c = a+b
				return c

a = int(input("Enter a : "))
b = int(input("Enter b : "))
addtemp = Template("Add a + b = {{ add(a=2, b=4) }}")
addition = addtemp.render(add=add)
print(addition)
