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


print "Module name is", __name__

class SomeClass:
    pass

print "Class inside names it as", repr( SomeClass.__module__ )

if __name__ == "__main__":
    print "Executed as __main__"

    import sys

    # The sys.argv[0]
    args = sys.argv[:]

    args[0] = args[0].replace( ".exe", ".py" )

    print "Arguments were", args

    import os
    print os.environ
