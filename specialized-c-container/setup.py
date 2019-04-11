from distutils.core import setup, Extension


setup(name = 'NuitkaListModule' , version = '1.0' , \
   ext_modules = [Extension('NuitkaListModule',['NuitkaAPI.c','list2.c'])])

setup(name = 'myModule', version = '1.0',  \
   ext_modules = [Extension('myModule', ['list1.c'])])
