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
# -*- coding: utf-8 -*-

def closureTest1():
    # Assign, but the value is not supposed to be used.
    d = 1

    def subby():
        return d

    d = 22222*2222

    return subby()


def closureTest2():
    # Using a closure variable that is not initialized at the time it is closured.

    def subby():
        return d

    d = 22222*22222

    return subby()


var1 = closureTest1()
var2 = closureTest2()

print var1
print var2