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

import sys, gc

def simpleFunction1():
    def abc(*, exc=IOError):
        pass
    for _ in range(100):
        abc()

def simpleFunction2():
    def abc(*, exc=IOError):
        raise ValueError from None

    try:
        abc()
    except (ValueError, TypeError):
        pass


m1 = {}
m2 = {}

def snapObjRefCntMap( before ):
   if before:
      global m1
      m = m1
   else:
      global m2
      m = m2

   for x in gc.get_objects():
      if x is m1:
         continue

      if x is m2:
         continue

      m[ str( x ) ] = sys.getrefcount( x )


def checkReferenceCount( checked_function, max_rounds = 10 ):
   assert sys.exc_info() == ( None, None, None ), sys.exc_info()

   print( checked_function.__name__ + ":", end = "" )

   ref_count1 = 17
   ref_count2 = 17

   explain = False

   for count in range( max_rounds ):
      x1 = 0
      x2 = 0

      gc.collect()
      ref_count1 = sys.gettotalrefcount()

      if explain and count == max_rounds - 1:
         snapObjRefCntMap( True )

      checked_function()

      assert sys.exc_info() == ( None, None, None ), sys.exc_info()

      gc.collect()

      if explain and count == max_rounds - 1:
         snapObjRefCntMap( False )

      ref_count2 = sys.gettotalrefcount()

      if ref_count1 == ref_count2:
         print( "PASSED" )
         break

      # print count, ref_count1, ref_count2
   else:
      print( "FAILED", ref_count1, ref_count2, "leaked", ref_count2 - ref_count1 )

      if explain:
         assert m1
         assert m2

         for key in m1.keys():
            if key not in m2:
               print( "*" * 80 )
               print( key )
            elif m1[key] != m2[key]:
               print( "*" * 80 )
               print( key )
            else:
               pass
               # print m1[key]

   assert sys.exc_info() == ( None, None, None ), sys.exc_info()

   gc.collect()

checkReferenceCount( simpleFunction1 )
checkReferenceCount( simpleFunction2 )
