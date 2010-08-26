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
# This taken from CPython's pystone test, and is an extract of it I made
# to analyse the differences between CPython and Nuitka performance. It
# was under PSF 2 license. It's not very useful anymore.

from time import clock

LOOPS = 5000000
__version__ = "1.1"


Char1Glob = '\0'
Char2Glob = '\0'

BoolGlob = 0

def Proc4():
    global Char2Glob

    BoolLoc = Char1Glob == 'A'
    BoolLoc = BoolLoc or BoolGlob
    Char2Glob = 'B'

def pystones(loops):
    return Proc0(loops)

def Proc0(loops):

    starttime = clock()
    for i in range(loops):
        pass
    nulltime = clock() - starttime

    starttime = clock()

    for i in range(loops):
        Proc4()

    benchtime = clock() - starttime - nulltime
    return benchtime, (loops / benchtime)

if __name__ == "__main__":
    benchtime, stones = pystones( LOOPS )
    print "Pystone(%s) time for %d passes = %g" % \
          (__version__, LOOPS, benchtime)
    print "This machine benchmarks at %g pystones/second" % stones
