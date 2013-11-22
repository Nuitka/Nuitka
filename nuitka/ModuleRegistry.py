#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
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
""" This to keep track of used modules.

    There is a set of root modules, which are user specified, and must be
    processed. As they go, they add more modules to active modules list
    and move done modules out of it.

    That process can be started.
"""

from nuitka.oset import OrderedSet

root_modules = OrderedSet()

def addRootModule( module ):
    root_modules.add( module )

def getRootModules():
    return root_modules

active_modules = OrderedSet()
done_modules = OrderedSet()

def startTraversal():
    # Using global here, as this is really a singleton, in the form of a module,
    # pylint: disable=W0603
    global active_modules, done_modules

    active_modules = OrderedSet( root_modules )
    done_modules = OrderedSet()

    for active_module in active_modules:
        active_module.startTraversal()

def addUsedModule( module ):
    if module not in done_modules and module not in active_modules:
        active_modules.add( module )
        module.startTraversal()

def nextModule():
    if active_modules:
        result = active_modules.pop()
        done_modules.add( result )

        return result
    else:
        return None

def remainingCount():
    return len( active_modules )

def getDoneModules():
    return list( done_modules )

shared_libraries = {}

def addSharedLibrary( package_name, module_name, filename ):
    if package_name is None:
        shared_libraries[ module_name ] = filename
    else:
        shared_libraries[ package_name + "." + module_name ] = filename
