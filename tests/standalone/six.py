from __future__ import absolute_import
import six
import sys
from logging import handlers


PY3 = sys.version_info[0] == 3
if PY3:
 string_types = str,
 integer_types = int,
 class_types = type


def dispatch_types(value):
   
    if isinstance(value, six.integer_types):
        print(value)

    elif isinstance(value, six.string_types):
        print(value)
        
    elif isinstance(value, six.class_types):
        value
        

def import_module(name):
    __import__(name)
    return sys.modules[name]
    

def add_doc(func, doc):
    print(func.__doc__) 


def main():
    dispatch_types(6)
    dispatch_types('hi')
    
    class X():
        pass
    
    p1 = X()
    
    dispatch_types(p1) 

    import_module("logging.handlers")
     
    def f():
      """Icky doc"""
      pass

    add_doc(f, """New doc""")


if __name__ == "__main__":
    main()


