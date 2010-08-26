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

print myname
