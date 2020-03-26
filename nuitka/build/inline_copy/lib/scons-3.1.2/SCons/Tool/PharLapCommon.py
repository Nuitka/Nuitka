"""SCons.Tool.PharLapCommon

This module contains common code used by all Tools for the
Phar Lap ETS tool chain.  Right now, this is linkloc and
386asm.

"""

#
# Copyright (c) 2001 - 2019 The SCons Foundation
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

__revision__ = "src/engine/SCons/Tool/PharLapCommon.py bee7caf9defd6e108fc2998a2520ddb36a967691 2019-12-17 02:07:09 bdeegan"

import os
import os.path
import SCons.Errors
import SCons.Util
import re

def getPharLapPath():
    """Reads the registry to find the installed path of the Phar Lap ETS
    development kit.

    Raises UserError if no installed version of Phar Lap can
    be found."""

    if not SCons.Util.can_read_reg:
        raise SCons.Errors.InternalError("No Windows registry module was found")
    try:
        k=SCons.Util.RegOpenKeyEx(SCons.Util.HKEY_LOCAL_MACHINE,
                                  'SOFTWARE\\Pharlap\\ETS')
        val, type = SCons.Util.RegQueryValueEx(k, 'BaseDir')

        # The following is a hack...there is (not surprisingly)
        # an odd issue in the Phar Lap plug in that inserts
        # a bunch of junk data after the phar lap path in the
        # registry.  We must trim it.
        idx=val.find('\0')
        if idx >= 0:
            val = val[:idx]
                    
        return os.path.normpath(val)
    except SCons.Util.RegError:
        raise SCons.Errors.UserError("Cannot find Phar Lap ETS path in the registry.  Is it installed properly?")

REGEX_ETS_VER = re.compile(r'#define\s+ETS_VER\s+([0-9]+)')

def getPharLapVersion():
    """Returns the version of the installed ETS Tool Suite as a
    decimal number.  This version comes from the ETS_VER #define in
    the embkern.h header.  For example, '#define ETS_VER 1010' (which
    is what Phar Lap 10.1 defines) would cause this method to return
    1010. Phar Lap 9.1 does not have such a #define, but this method
    will return 910 as a default.

    Raises UserError if no installed version of Phar Lap can
    be found."""

    include_path = os.path.join(getPharLapPath(), os.path.normpath("include/embkern.h"))
    if not os.path.exists(include_path):
        raise SCons.Errors.UserError("Cannot find embkern.h in ETS include directory.\nIs Phar Lap ETS installed properly?")
    with open(include_path, 'r') as f:
        mo = REGEX_ETS_VER.search(f.read())
    if mo:
        return int(mo.group(1))
    # Default return for Phar Lap 9.1
    return 910

def addPharLapPaths(env):
    """This function adds the path to the Phar Lap binaries, includes,
    and libraries, if they are not already there."""
    ph_path = getPharLapPath()

    try:
        env_dict = env['ENV']
    except KeyError:
        env_dict = {}
        env['ENV'] = env_dict
    SCons.Util.AddPathIfNotExists(env_dict, 'PATH',
                                  os.path.join(ph_path, 'bin'))
    SCons.Util.AddPathIfNotExists(env_dict, 'INCLUDE',
                                  os.path.join(ph_path, 'include'))
    SCons.Util.AddPathIfNotExists(env_dict, 'LIB',
                                  os.path.join(ph_path, 'lib'))
    SCons.Util.AddPathIfNotExists(env_dict, 'LIB',
                                  os.path.join(ph_path, os.path.normpath('lib/vclib')))
    
    env['PHARLAP_PATH'] = getPharLapPath()
    env['PHARLAP_VERSION'] = str(getPharLapVersion())
    

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
