#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.__past__ import StringIO

from . import Tracing


def _indent(elem, level=0, more_sibs=False):
    i = "\n"
    if level:
        i += (level - 1) * "  "
    num_kids = len(elem)
    if num_kids:
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
            if level:
                elem.text += "  "
        count = 0
        for kid in elem:
            _indent(kid, level + 1, count < num_kids - 1)
            count += 1
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
            if more_sibs:
                elem.tail += "  "
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
            if more_sibs:
                elem.tail += "  "

    return elem


def _dedent(elem, level=0):
    if not elem.text or not elem.text.strip():
        elem.text = ""

    for child in elem:
        _dedent(child, level + 1)

    if not elem.tail or not elem.tail.strip():
        elem.tail = ""

    return elem


try:
    import xml.etree.ElementTree

    xml_module = xml.etree.ElementTree

    Element = xml.etree.ElementTree.Element

    def xml_tostring(tree, indent=True):
        if indent:
            _indent(tree)
        elif not indent:
            _dedent(tree)

        return xml_module.tostring(tree)

except ImportError:
    xml_module = None
    Element = None
    xml_tostring = None

# TODO: Use the writer to create the XML we output. That should be more
# scalable and/or faster.
try:
    import lxml.xmlfile  # pylint: disable=I0021,import-error

    xml_writer = lxml.xmlfile
except ImportError:
    xml_writer = None


def toBytes(tree, indent=True):
    return xml_tostring(tree, indent=indent)


def toString(tree):
    result = toBytes(tree)

    if str is not bytes:
        result = result.decode("utf8")

    return result


def fromString(text):
    return xml_module.parse(StringIO(text)).getroot()


def dump(tree):
    value = toString(tree).rstrip()

    Tracing.printLine(value)
