"""SCons.Tool.gfortran

Tool-specific initialization for gfortran, the GNU Fortran 95/Fortran
2003 compiler.

There normally shouldn't be any need to import this module directly.
It will usually be imported through the generic SCons.Tool.Tool()
selection method.

"""

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

__revision__ = "src/engine/SCons/Tool/gfortran.py  2014/07/05 09:42:21 garyo"

import SCons.Util

import fortran

def generate(env):
    """Add Builders and construction variables for gfortran to an
    Environment."""
    fortran.generate(env)

    for dialect in ['F77', 'F90', 'FORTRAN', 'F95', 'F03']:
        env['%s' % dialect] = 'gfortran'
        env['SH%s' % dialect] = '$%s' % dialect
        if env['PLATFORM'] in ['cygwin', 'win32']:
            env['SH%sFLAGS' % dialect] = SCons.Util.CLVar('$%sFLAGS' % dialect)
        else:
            env['SH%sFLAGS' % dialect] = SCons.Util.CLVar('$%sFLAGS -fPIC' % dialect)

        env['INC%sPREFIX' % dialect] = "-I"
        env['INC%sSUFFIX' % dialect] = ""

def exists(env):
    return env.Detect('gfortran')

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
