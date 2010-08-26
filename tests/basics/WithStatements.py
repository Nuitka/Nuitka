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

x = 0

class MyContextManager:
    def __enter__( self ):
        global x
        x += 1

        print "Entered context manager", x

        return x

    def __exit__( self, exc_type, exc_value, traceback ):
        print exc_type, exc_value, traceback

        return False

with MyContextManager() as x:
    print "x has become", x

try:
    with MyContextManager() as x:
        print "x has become", x

        raise Exception( "Lalala" )
        print x
except Exception, e:
    print e
