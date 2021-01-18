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


def indent(elem, level=0, more_sibs=False):
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
            indent(kid, level + 1, count < num_kids - 1)
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


try:
    import lxml.etree  # pylint: disable=I0021,import-error

    xml_module = lxml.etree

    Element = xml_module.Element
    xml_tostring = lambda tree: lxml.etree.tostring(tree, pretty_print=True)
except ImportError:
    try:
        import xml.etree.ElementTree

        xml_module = xml.etree.ElementTree

        Element = xml.etree.ElementTree.Element
        xml_tostring = lambda tree: xml_module.tostring(indent(tree))
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


def toBytes(tree):
    return xml_tostring(tree)


def toString(tree):
    result = toBytes(tree)

    if str is not bytes:
        result = result.decode("utf-8")

    return result


def fromString(text):
    return xml_module.parse(StringIO(text)).getroot()


def dump(tree):
    value = toString(tree).rstrip()

    Tracing.printLine(value)
