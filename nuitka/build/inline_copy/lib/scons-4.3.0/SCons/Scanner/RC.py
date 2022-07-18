# MIT License
#
# Copyright The SCons Foundation
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Dependency scanner for RC (Interface Definition Language) files."""


import SCons.Node.FS
from . import ClassicCPP


def no_tlb(nodes):
    """Filter out .tlb files as they are binary and shouldn't be scanned."""

    # print("Nodes:%s"%[str(n) for n in nodes])
    return [n for n in nodes if str(n)[-4:] != '.tlb']


def RCScan():
    """Return a prototype Scanner instance for scanning RC source files"""

    res_re = (
        r'^(?:\s*#\s*(?:include)|'
        r'.*?\s+(?:ICON|BITMAP|CURSOR|HTML|FONT|MESSAGETABLE|TYPELIB|REGISTRY|D3DFX)'
        r'\s*.*?)'
        r'\s*(<|"| )([^>"\s]+)(?:[>"\s])*$'
    )
    resScanner = ClassicCPP(
        "ResourceScanner", "$RCSUFFIXES", "CPPPATH", res_re, recursive=no_tlb
    )

    return resScanner

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
