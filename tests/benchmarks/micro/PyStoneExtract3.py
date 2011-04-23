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
# This taken from CPython's pystone test, and is an extract of it I made to analyse the
# differences between CPython and Nuitka performance. It was under PSF 2 license. It's not
# very useful anymore, but it is under that license still.

LOOPS = 50000

class Record:

    def __init__(self, PtrComp = None, Discr = 0, EnumComp = 0,
                       IntComp = 0, StringComp = 0):
        self.PtrComp = PtrComp
        self.Discr = Discr
        self.EnumComp = EnumComp
        self.IntComp = IntComp
        self.StringComp = StringComp

    def copy(self):
        return Record(self.PtrComp, self.Discr, self.EnumComp,
                      self.IntComp, self.StringComp)


def Proc1(PtrParIn):
    PtrParIn.PtrComp = NextRecord = PtrGlb.copy()
    PtrParIn.IntComp = 5
    NextRecord.IntComp = PtrParIn.IntComp
    NextRecord.PtrComp = PtrParIn.PtrComp

    if NextRecord.Discr == 17:
        NextRecord.IntComp = 6
        NextRecord.EnumComp = Proc6(PtrParIn.EnumComp)
        NextRecord.PtrComp = PtrGlb.PtrComp
        NextRecord.IntComp = Proc7(NextRecord.IntComp, 10)
    else:
        PtrParIn = NextRecord.copy()

    NextRecord.PtrComp = None
    return PtrParIn

def benchmark( loops ):
    global PtrGlb
    global PtrGlbNext

    PtrGlb = Record()

    for i in xrange( loops ):
        PtrGlb = Proc1(PtrGlb)

if __name__ == '__main__':
    benchmark( LOOPS )
