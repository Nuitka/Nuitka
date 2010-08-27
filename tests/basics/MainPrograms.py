#
#     Kay Hayen, mailto:kayhayen@gmx.de
#
#     Python test originally created or extracted from other peoples work. The
#     parts from me are in the public domain. It is at least Free Software
#     where it's copied from other people. In these cases, it will normally be
#     indicated.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
#
#     Please leave the whole of this copyright notice intact.
#


print "Module name is", __name__

class SomeClass:
    pass

print "Class inside names it as", repr( SomeClass.__module__ )

if __name__ == "__main__":
    print "Executed as __main__"

    import sys, os

    # The sys.argv[0]
    args = sys.argv[:]

    args[0] = os.path.basename( args[0] ).replace( ".exe", ".py" )

    print "Arguments were", args

    import os
    print sorted( os.environ )
