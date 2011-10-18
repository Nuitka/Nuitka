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
def localImporter1():
    import os

    return os

def localImporter1a():
    import os as my_os_name

    return my_os_name


def localImporter2():
    from os import path

    return path

def localImporter2a():
    from os import path as renamed

    return renamed

print "Direct module import", localImporter1()
print "Direct module import using rename", localImporter1a()

print "From module import", localImporter2()
print "From module import using rename", localImporter2a()

from os import *

print "Star import gave us", path

import os.path as myname

print "As import gave", myname

def localImportFailure():
    try:
        from os import path, lala, listdir
    except Exception as e:
        print type(e), e

    try:
        print listdir
    except UnboundLocalError:
        print " and listdir was not imported",

    print "but path was", path

print "From import that fails in the middle", localImportFailure()
