"""SCons.Tool.aixc++

Tool-specific initialization for IBM xlC / Visual Age C++ compiler.

There normally shouldn't be any need to import this module directly.
It will usually be imported through the generic SCons.Tool.Tool()
selection method.

"""

#
# __COPYRIGHT__
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

__revision__ = "__FILE__ __REVISION__ __DATE__ __DEVELOPER__"

import os.path

import SCons.Platform.aix

import SCons.Tool.cxx
cplusplus = SCons.Tool.cxx
#cplusplus = __import__('cxx', globals(), locals(), [])

packages = ['vacpp.cmp.core', 'vacpp.cmp.batch', 'vacpp.cmp.C', 'ibmcxx.cmp']

def get_xlc(env):
    xlc = env.get('CXX', 'xlC')
    return SCons.Platform.aix.get_xlc(env, xlc, packages)

def generate(env):
    """Add Builders and construction variables for xlC / Visual Age
    suite to an Environment."""
    path, _cxx, version = get_xlc(env)
    if path and _cxx:
        _cxx = os.path.join(path, _cxx)

    if 'CXX' not in env:
        env['CXX'] = _cxx

    cplusplus.generate(env)

    if version:
        env['CXXVERSION'] = version
    
def exists(env):
    path, _cxx, version = get_xlc(env)
    if path and _cxx:
        xlc = os.path.join(path, _cxx)
        if os.path.exists(xlc):
            return xlc
    return None

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
