#
# Copyright (c) 2001 - 2014 The SCons Foundation
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
#

__revision__ = "src/engine/SCons/Options/BoolOption.py  2014/07/05 09:42:21 garyo"

__doc__ = """Place-holder for the old SCons.Options module hierarchy

This is for backwards compatibility.  The new equivalent is the Variables/
class hierarchy.  These will have deprecation warnings added (some day),
and will then be removed entirely (some day).
"""

import SCons.Variables
import SCons.Warnings

warned = False

def BoolOption(*args, **kw):
    global warned
    if not warned:
        msg = "The BoolOption() function is deprecated; use the BoolVariable() function instead."
        SCons.Warnings.warn(SCons.Warnings.DeprecatedOptionsWarning, msg)
        warned = True
    return SCons.Variables.BoolVariable(*args, **kw)

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
