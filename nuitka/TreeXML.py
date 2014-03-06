#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" XML node tree handling

Means to create XML elements from Nuitka tree nodes and to convert the
XML tree to ASCII or output it.
"""

from nuitka import Tracing, Utils

try:
    import lxml.etree
except ImportError:
    lxml = None

def toString(xml):
    return lxml.etree.tostring( xml, pretty_print = True )

def dump(xml ):
    value = toString( xml ).rstrip()

    if Utils.python_version >= 300:
        value = value.decode( "utf-8" )

    Tracing.printLine( value )
