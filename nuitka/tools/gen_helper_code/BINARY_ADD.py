from jinja2 import Template

def isIntTypeExact(a):
	if(isinstance(a,str)):
		return 0
	else:
		if (type(int(a)))==int:
			if(isinstance(a,float)):
				print("Not an Integer")
			else:
				return 1

def add(a, b):
	return a+b

def concat(a, b):
	return a+b


checkIntopa = Template("{{ isIntTypeExact(a=3) }}")
resa = checkIntopa.render(isIntTypeExact=isIntTypeExact)

checkIntopb = Template("{{isIntTypeExact(a=5) }}")
resb = checkIntopb.render(isIntTypeExact=isIntTypeExact)

result = ""

if(resa == '1'):
	if(resb == '1'):
		addtemp = Template("{{ add(a=2, b=5) }}")
		result = addtemp.render(add=add)	
elif(resa == '0'):
	if(resb == '0'):
		concat_temp = Template("{{ concat(a='2', b='5') }}")
		result = concat_temp.render(concat=concat)

print(result)

"""
addtemp = Template("Add a + b = {{ add(a=2, b=4) }}")
add = addtemp.render(add=add)
print(add)
"""