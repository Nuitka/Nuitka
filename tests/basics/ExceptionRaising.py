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
def raiseExceptionClass():
    raise ValueError

try:
    raiseExceptionClass()
except Exception, e:
    print e, repr(e), type(e)

def raiseExceptionInstance():
    raise ValueError( "hallo" )

try:
    raiseExceptionInstance()
except Exception, f:
    print f, repr(f), type(f)


def raiseExceptionAndReraise():
    try:
       x = 0
       y = x / x

    except:
      raise
try:
    raiseExceptionAndReraise()
except:
    print "Catched reraised"

def raiseNonGlobalError():
    return undefined_value

try:
   raiseNonGlobalError()
except:
   print "NameError caught"

def raiseIllegalError():
    class X(object):
        pass

    raise X()

try:
    raiseIllegalError()
except TypeError, E:
    print "new style class exception was rejected:", E
except:
    assert False, "Error, new style class exception was not rejected"

def raiseCustomError():
    raise ClassicClassException()

class ClassicClassException:
    pass

try:
    raiseCustomError()
except ClassicClassException:
    print "Caught classic class exception"
except:
    assert False, "Error, old style class exception was not caught"
