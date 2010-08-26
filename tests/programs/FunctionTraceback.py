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

# Just plain exception from the module level, supposed to report the correct file and line



def generator_function():
    import ErrorRaising

    x = ( lambda : ErrorRaising.raiseException() for z in range(3) )

    x.next()()


def normal_function():
    y = generator_function()

    y()

normal_function()
