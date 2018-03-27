#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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

def starImporterFunction():
    from sys import *  # @UnusedWildImport

    print "Version", version.split()[0].split('.')[:-1]

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

            print "Closure one level up was taken", for_closure_as_well
            print "Closure two levels up was taken", for_closure
            print "Globals still work", starImporterFunction
            print "Added local from code", f  # @UndefinedVariable

        execFunction()

    deeper()

deepExec()
