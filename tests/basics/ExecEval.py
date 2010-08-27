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

print "eval 3+3=", eval("3+3")
print "eval  3+3=", eval(" 3+3")

def functionEval1():
    return eval(" 3+3")

print "eval in a function with nothing provided", functionEval1()

def functionEval2():
    a = [2]

    g = {}

    r = eval( "1+3", g )

    return r, g.keys()

print "eval in a function with globals provided", functionEval2()

def functionEval3():
    result = []

    for x in eval( "(1,2)"):
        result.append( x )

    return result

print "eval in a for loop as iterator giver", functionEval3()

print "exec on a global level",
exec( "d=2+2" )
print "2+2=",d

def functionExec1():
    a = 1

    exec( "a=2" )

    return a

def functionExec2():
    a = 1

    exec "a=2" in globals(), locals()

    return a

print "exec in function with and with locals() provided:", functionExec1(), functionExec2()

f = open( "/tmp/execfile.py", "wb" )
f.write( "e=7\nf=8\n" )
f.close()

execfile( "/tmp/execfile.py" )

print "execfile with defaults f,g=", e, f

global_vars = { 'e' : '0', 'f' : 0 }
local_vars = dict( global_vars )

execfile( "/tmp/execfile.py", global_vars )

print "execfile with globals dict:", global_vars.keys()

execfile( "/tmp/execfile.py", global_vars, local_vars )

print "execfile with globals and locals dict:", local_vars

def functionExecfile():
    e = 0
    f = 0

    global_vars = { 'e' : '0', 'f' : 0 }
    local_vars = dict( global_vars )

    execfile( "/tmp/execfile.py", global_vars, local_vars )

    print "execfile with globals and locals dict in a function:", global_vars.keys(), local_vars, e, f

functionExecfile()
