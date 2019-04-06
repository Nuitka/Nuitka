from __future__ import print_function

import os

def submodule11_f1( var1 ):
    print_str = "" + __name__ + " : function submodule11_f1: " +  var1
    print(print_str, end='')
    print()

def submodule11_f2( var1 ):
    print_str = "" + __name__ + " : function submodule11_f2: " +  var1
    print(print_str)
    print("printing package data!!")
    with open(os.path.join(os.path.dirname(__file__), 'data.txt')) as f:
        print(f.read())

