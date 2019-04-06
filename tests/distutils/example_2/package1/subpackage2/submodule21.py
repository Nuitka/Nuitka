from __future__ import print_function
from package1.subpackage1.submodule11 import submodule11_f1

def submodule21_f1( var1 ):
    print_str = "" + __name__ + " : function submodule21_f1: " +  var1 + " "
    print(print_str, end='')
    submodule11_f1(var1)
    print()
