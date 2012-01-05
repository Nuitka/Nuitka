#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Python test originally created or extracted from other peoples work. The
#     parts and resulting tests are too small to be protected and therefore
#     is in the public domain.
#
#     If you submit Kay Hayen patches to this in either form, you automatically
#     grant him a copyright assignment to the code, or in the alternative a BSD
#     license to the code, should your jurisdiction prevent this. Obviously it
#     won't affect code that comes to him indirectly or code you don't submit to
#     him.
#
#     This is to reserve my ability to re-license the official code at any time,
#     to put it into public domain or under PSF.
#
#     Please leave the whole of this copyright notice intact.
#

def starImporterFunction():
    from sys import *

    print "Version", version.split()[0]

starImporterFunction()

def deepExec():
    for_closure = 3

    def deeper():
        for_closure_as_well = 4

        def execFunction():
            code = "f=2"

            # Can fool it to nest
            exec code in None, None

            print "Locals now", locals()

            # print "Closure one level up was taken", for_closure_as_well
            # print "Closure two levels up was taken", for_closure
            print "Globals still work", starImporterFunction
            print "Added local from code", f

        execFunction()

    deeper()

deepExec()
