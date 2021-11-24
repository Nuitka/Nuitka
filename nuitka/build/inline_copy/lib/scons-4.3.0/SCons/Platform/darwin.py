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

"""Platform-specific initialization for Mac OS X systems.

There normally shouldn't be any need to import this module directly.  It
will usually be imported through the generic SCons.Platform.Platform()
selection method.
"""

from . import posix
import os

def generate(env):
    posix.generate(env)
    env['SHLIBSUFFIX'] = '.dylib'
    env['HOST_OS'] = 'darwin'
    # put macports paths at front to override Apple's versions, fink path is after
    # For now let people who want Macports or Fink tools specify it!
    # env['ENV']['PATH'] = '/opt/local/bin:/opt/local/sbin:' + env['ENV']['PATH'] + ':/sw/bin'
    
    # Store extra system paths in env['ENV']['PATHOSX']
    
    filelist = ['/etc/paths',]
    # make sure this works on Macs with Tiger or earlier
    try:
        dirlist = os.listdir('/etc/paths.d')
    except FileNotFoundError:
        dirlist = []

    for file in dirlist:
        filelist.append('/etc/paths.d/'+file)

    for file in filelist:
        if os.path.isfile(file):
            with open(file, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if line:
                        env.AppendENVPath('PATHOSX', line.strip('\n'))

    # Not sure why this wasn't the case all along?
    if env['ENV'].get('PATHOSX', False) and os.environ.get('SCONS_USE_MAC_PATHS', False):
        env.AppendENVPath('PATH',env['ENV']['PATHOSX'])

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
