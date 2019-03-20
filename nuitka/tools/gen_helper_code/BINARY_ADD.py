

import jinja2

"""
def BINARY_ADDITION(a, b):
	if(isinstance(a,str)):
		print("Not an integer") 
	else:
		if (type(int(a)))==int:
			if(isinstance(a,float)):
				print("Not an Integer")
			else:
				c = a+b
				return c
"""
macro = ("{% macro add(a,b) %}"
			"{# if PYTHON_VERSION < 300 #}"
         		"{% if a is number %}"
         			"{% if b|int !=0 %}"
         				"{{ a+b }}"
         			"{% endif %}"
         		"{% endif %}"
         	"{# endif #}"
        "{% endmacro %}")
use_macro = "Add a + b = {{ add(a=2,b=5)}}"
loader = jinja2.DictLoader({'template': use_macro})
env = jinja2.Environment(loader=loader)
macro_template = env.from_string(macro)
env.globals['add'] = macro_template.module.add
template = env.get_template('template')
rendered = template.render()
print(rendered)