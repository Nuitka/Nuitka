#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Python tests originally created or extracted from other peoples work. The
#     parts were too small to be protected.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#

x = 0

# This is used to trace the exact interaction with the context manager to uncover and
# decide orddering and correctness of calls.
class MyContextManager(object):
    def __getattribute__(self, attribute_name):
        print "Asking context manager attribute", attribute_name
        return object.__getattribute__( self, attribute_name )

    def __enter__(self):
        global x
        x += 1

        print "Entered context manager with counter value", x

        return x

    def __exit__(self, exc_type, exc_value, traceback):
        print "Exit sees", exc_type, exc_value, traceback

        return False

print "Use context manager and raise exception in the body:"
with MyContextManager() as x:
    print "x has become", x

try:
    with MyContextManager() as x:
        print "x has become", x

        raise Exception( "Lalala" )
        print x
except Exception, e:
    print "Caught raised exception", repr(e)

l = range(3)

print "Use context manager and assign to subscription target:"
with MyContextManager() as l[0]:
    print "Complex assignment target works", l[0]

try:
    import sys
    with MyContextManager():
        sys.exit(9)
except BaseException as e:
    print "Caught base exception", repr(e)


print "Use context manager and fail to assign to attribute:"
try:
    import sys
    with MyContextManager() as l.wontwork:
        sys.exit(9)
except BaseException as e:
    print "Caught base exception", repr(e)

print "Use context manager to do nothing inside:"
with MyContextManager() as x:
    pass

# Use context manager and fail to assign.
def returnFromContextBlock():
    # Use context manager to do nothing.
    with MyContextManager() as x:
        return 7

print "Use context manager to return value:"
r = returnFromContextBlock()
print "Return value", r

class NonContextManager1:
    def __enter__(self):
        return self

class NonContextManager2:
    def __exit__(self):
        return self

try:
    with NonContextManager1() as x:
        print x
except Exception, e:
    print repr(e)

try:
    with NonContextManager2() as x:
        print x
except Exception, e:
    print repr(e)

class NotAtAllContextManager:
    pass

try:
    with NotAtAllContextManager() as x:
        print x
except Exception, e:
    print repr(e)

class MeanContextManager:
    def __enter__(self):
        raise ValueError( "Nah, I won't play" )

    def __exit__(self):
        print "Called exit, yes"

try:
    with MeanContextManager() as x:
        print x
except Exception, e:
    print repr(e)
