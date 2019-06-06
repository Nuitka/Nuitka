#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
print( "some_package.star_importing, doing the star import" )

print("Before", sorted(x for x in dir() if x != "__compiled__"))

from .pyexpat import *  # @UnusedWildImport

lala = 1
print("After", sorted(x for x in dir() if x != "__compiled__"))

print( "Finished" )
