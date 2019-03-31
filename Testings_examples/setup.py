from distutils.core import setup, Extension

setup(name = 'myModule', version = '1.0',  \
   ext_modules = [Extension('myModule', ['Specialized_C_containers.c'])])
