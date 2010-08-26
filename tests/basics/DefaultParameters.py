# 
#     Kay Hayen, mailto:kayhayen@gmx.de
# 
#     Python test that I originally created or extracted from other peoples
#     work. I put my parts of it in the public domain. It is at least Free
#     Software where it's copied from other people. In these cases, I will
#     indicate it.
# 
#     If you submit patches to this software in either form, you automatically
#     grant me a copyright assignment to the new code, or in the alternative
#     a BSD license to the new code, should your jurisdiction prevent this. This
#     is to reserve my ability to re-license the code at any time.
# 

module_level = 1

def defaultValueTest1( no_default, some_default_constant = 1 ):
    return some_default_constant
    
def defaultValueTest2( no_default, some_default_constant = module_level*2 ):
    local_var = no_default = "1"
    return local_var, some_default_constant
    
def defaultValueTest3( no_default, funced_defaulted = defaultValueTest1(module_level)):
    return [ funced_defaulted for i in range(8) ]

##def defaultValueTest4( no_default, funced_defaulted = lambda x: x**2):
##    c = 1
##    d = 1
##    return ( i+c+d for i in range(8) )
##
##def defaultValueTest5( no_default, tuple_defaulted = (1,2,3)):
##    pass
##
##def defaultValueTest6( no_default, list_defaulted = [1,2,3]):
##    pass

print defaultValueTest1("ignored")

# The change of the default variable doesn't influence the default
# parameter of defaultValueTest2, that means it's also calculated
# at the time the function is defined.
module_level = 7
print defaultValueTest2("also ignored")

print defaultValueTest3("nono not again")
