#
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
#
"""Module for Visual C/C++ detection and configuration.

# TODO:
#   * gather all the information from a single vswhere call instead
#     of calling repeatedly (use json format?)
#   * support passing/setting location for vswhere in env.
#   * supported arch for versions: for old versions of batch file without
#     argument, giving bogus argument cannot be detected, so we have to hardcode
#     this here
#   * print warning when msvc version specified but not found
#   * find out why warning do not print
#   * test on 64 bits XP +  VS 2005 (and VS 6 if possible)
#   * SDK
#   * Assembly
"""

import SCons.compat
import SCons.Util

import subprocess
import os
import platform
from string import digits as string_digits
from subprocess import PIPE

import SCons.Warnings
from SCons.Tool import find_program_path

from . import common
from .common import CONFIG_CACHE, debug
from .sdk import get_installed_sdks


class VisualCException(Exception):
    pass

class UnsupportedVersion(VisualCException):
    pass

class MSVCUnsupportedHostArch(VisualCException):
    pass

class MSVCUnsupportedTargetArch(VisualCException):
    pass

class MissingConfiguration(VisualCException):
    pass

class NoVersionFound(VisualCException):
    pass

class BatchFileExecutionError(VisualCException):
    pass

# Dict to 'canonalize' the arch
_ARCH_TO_CANONICAL = {
    "amd64"     : "amd64",
    "emt64"     : "amd64",
    "i386"      : "x86",
    "i486"      : "x86",
    "i586"      : "x86",
    "i686"      : "x86",
    "ia64"      : "ia64",      # deprecated
    "itanium"   : "ia64",      # deprecated
    "x86"       : "x86",
    "x86_64"    : "amd64",
    "arm"       : "arm",
    "arm64"     : "arm64",
    "aarch64"   : "arm64",
}

# Starting with 14.1 (aka VS2017), the tools are organized by host directory.
# subdirs for each target. They are now in .../VC/Auxuiliary/Build.
# Note 2017 Express uses Hostx86 even if it's on 64-bit Windows,
# not reflected in this table.
_HOST_TARGET_TO_CL_DIR_GREATER_THAN_14 = {
    ("arm64","arm64")  : ("Hostarm64","arm64"),
    ("amd64","amd64")  : ("Hostx64","x64"),
    ("amd64","x86")    : ("Hostx64","x86"),
    ("amd64","arm")    : ("Hostx64","arm"),
    ("amd64","arm64")  : ("Hostx64","arm64"),
    ("x86","amd64")    : ("Hostx86","x64"),
    ("x86","x86")      : ("Hostx86","x86"),
    ("x86","arm")      : ("Hostx86","arm"),
    ("x86","arm64")    : ("Hostx86","arm64"),
}

# before 14.1 (VS2017): the original x86 tools are in the tools dir,
# any others are in a subdir named by the host/target pair,
# or just a single word if host==target
_HOST_TARGET_TO_CL_DIR = {
    ("amd64","amd64")  : "amd64",
    ("amd64","x86")    : "amd64_x86",
    ("amd64","arm")    : "amd64_arm",
    ("amd64","arm64")  : "amd64_arm64",
    ("x86","amd64")    : "x86_amd64",
    ("x86","x86")      : "",
    ("x86","arm")      : "x86_arm",
    ("x86","arm64")    : "x86_arm64",
    ("arm","arm")      : "arm",
}

# 14.1 (VS2017) and later:
# Given a (host, target) tuple, return the batch file to look for.
# We can't rely on returning an arg to use for vcvarsall.bat,
# because that script will run even if given a pair that isn't installed.
# Targets that already look like a pair are pseudo targets that
# effectively mean to skip whatever the host was specified as.
_HOST_TARGET_TO_BAT_ARCH_GT14 = {
    ("arm64", "arm64"): "vcvarsarm64.bat",
    ("amd64", "amd64"): "vcvars64.bat",
    ("amd64", "x86"): "vcvarsamd64_x86.bat",
    ("amd64", "x86_amd64"): "vcvarsx86_amd64.bat",
    ("amd64", "x86_x86"): "vcvars32.bat",
    ("amd64", "arm"): "vcvarsamd64_arm.bat",
    ("amd64", "x86_arm"): "vcvarsx86_arm.bat",
    ("amd64", "arm64"): "vcvarsamd64_arm64.bat",
    ("amd64", "x86_arm64"): "vcvarsx86_arm64.bat",
    ("x86", "x86"): "vcvars32.bat",
    ("x86", "amd64"): "vcvarsx86_amd64.bat",
    ("x86", "x86_amd64"): "vcvarsx86_amd64.bat",
    ("x86", "arm"): "vcvarsx86_arm.bat",
    ("x86", "x86_arm"): "vcvarsx86_arm.bat",
    ("x86", "arm64"): "vcvarsx86_arm64.bat",
    ("x86", "x86_arm64"): "vcvarsx86_arm64.bat",
}

# before 14.1 (VS2017):
# Given a (host, target) tuple, return the argument for the bat file;
# Both host and target should be canoncalized.
# If the target already looks like a pair, return it - these are
# pseudo targets (mainly used by Express versions)
_HOST_TARGET_ARCH_TO_BAT_ARCH = {
    ("x86", "x86"): "x86",
    ("x86", "amd64"): "x86_amd64",
    ("x86", "x86_amd64"): "x86_amd64",
    ("amd64", "x86_amd64"): "x86_amd64", # This is present in (at least) VS2012 express
    ("amd64", "amd64"): "amd64",
    ("amd64", "x86"): "x86",
    ("amd64", "x86_x86"): "x86",
    ("x86", "ia64"): "x86_ia64",         # gone since 14.0
    ("x86", "arm"): "x86_arm",          # since 14.0
    ("x86", "arm64"): "x86_arm64",      # since 14.1
    ("amd64", "arm"): "amd64_arm",      # since 14.0
    ("amd64", "arm64"): "amd64_arm64",  # since 14.1
    ("x86", "x86_arm"): "x86_arm",      # since 14.0
    ("x86", "x86_arm64"): "x86_arm64",  # since 14.1
    ("amd64", "x86_arm"): "x86_arm",      # since 14.0
    ("amd64", "x86_arm64"): "x86_arm64",  # since 14.1
    ("arm64", "arm64"): "arm64_arm64",  # since 14.3

}

_CL_EXE_NAME = 'cl.exe'

def get_msvc_version_numeric(msvc_version):
    """Get the raw version numbers from a MSVC_VERSION string, so it
    could be cast to float or other numeric values. For example, '14.0Exp'
    would get converted to '14.0'.

    Args:
        msvc_version: str
            string representing the version number, could contain non
            digit characters

    Returns:
        str: the value converted to a numeric only string

    """
    return ''.join([x for  x in msvc_version if x in string_digits + '.'])

def get_host_target(env):
    host_platform = env.get('HOST_ARCH')
    debug("HOST_ARCH:" + str(host_platform))
    if not host_platform:
        host_platform = platform.machine()

    # Solaris returns i86pc for both 32 and 64 bit architectures
    if host_platform == "i86pc":
        if platform.architecture()[0] == "64bit":
            host_platform = "amd64"
        else:
            host_platform = "x86"

    # Retain user requested TARGET_ARCH
    req_target_platform = env.get('TARGET_ARCH')
    debug("TARGET_ARCH:" + str(req_target_platform))
    if req_target_platform:
        # If user requested a specific platform then only try that one.
        target_platform = req_target_platform
    else:
        target_platform = host_platform

    try:
        host = _ARCH_TO_CANONICAL[host_platform.lower()]
    except KeyError:
        msg = "Unrecognized host architecture %s"
        raise MSVCUnsupportedHostArch(msg % repr(host_platform))

    try:
        target = _ARCH_TO_CANONICAL[target_platform.lower()]
    except KeyError:
        all_archs = str(list(_ARCH_TO_CANONICAL.keys()))
        raise MSVCUnsupportedTargetArch(
            "Unrecognized target architecture %s\n\tValid architectures: %s"
            % (target_platform, all_archs)
        )

    return (host, target, req_target_platform)

# If you update this, update SupportedVSList in Tool/MSCommon/vs.py, and the
# MSVC_VERSION documentation in Tool/msvc.xml.
_VCVER = [
    "14.3",
    "14.2",
    "14.1", "14.1Exp",
    "14.0", "14.0Exp",
    "12.0", "12.0Exp",
    "11.0", "11.0Exp",
    "10.0", "10.0Exp",
    "9.0", "9.0Exp",
    "8.0", "8.0Exp",
    "7.1",
    "7.0",
    "6.0"]

# if using vswhere, configure command line arguments to probe for installed VC editions
_VCVER_TO_VSWHERE_VER = {
    '14.3': [
        ["-version", "[17.0, 18.0)"],  # default: Enterprise, Professional, Community  (order unpredictable?)
        ["-version", "[17.0, 18.0)", "-products", "Microsoft.VisualStudio.Product.BuildTools"],  # BuildTools
    ],
    '14.2': [
        ["-version", "[16.0, 17.0)"],  # default: Enterprise, Professional, Community  (order unpredictable?)
        ["-version", "[16.0, 17.0)", "-products", "Microsoft.VisualStudio.Product.BuildTools"],  # BuildTools
    ],
    '14.1': [
        ["-version", "[15.0, 16.0)"],  # default: Enterprise, Professional, Community (order unpredictable?)
        ["-version", "[15.0, 16.0)", "-products", "Microsoft.VisualStudio.Product.BuildTools"],  # BuildTools
    ],
    '14.1Exp': [
        ["-version", "[15.0, 16.0)", "-products", "Microsoft.VisualStudio.Product.WDExpress"],  # Express
    ],
}

_VCVER_TO_PRODUCT_DIR = {
    '14.3': [
        (SCons.Util.HKEY_LOCAL_MACHINE, r'')],  # not set by this version
    '14.2': [
        (SCons.Util.HKEY_LOCAL_MACHINE, r'')],  # not set by this version
    '14.1': [
        (SCons.Util.HKEY_LOCAL_MACHINE, r'')],  # not set by this version
    '14.1Exp': [
        (SCons.Util.HKEY_LOCAL_MACHINE, r'')],  # not set by this version
    '14.0': [
        (SCons.Util.HKEY_LOCAL_MACHINE, r'Microsoft\VisualStudio\14.0\Setup\VC\ProductDir')],
    '14.0Exp': [
        (SCons.Util.HKEY_LOCAL_MACHINE, r'Microsoft\VCExpress\14.0\Setup\VC\ProductDir')],
    '12.0': [
        (SCons.Util.HKEY_LOCAL_MACHINE, r'Microsoft\VisualStudio\12.0\Setup\VC\ProductDir'),
    ],
    '12.0Exp': [
        (SCons.Util.HKEY_LOCAL_MACHINE, r'Microsoft\VCExpress\12.0\Setup\VC\ProductDir'),
    ],
    '11.0': [
        (SCons.Util.HKEY_LOCAL_MACHINE, r'Microsoft\VisualStudio\11.0\Setup\VC\ProductDir'),
    ],
    '11.0Exp': [
        (SCons.Util.HKEY_LOCAL_MACHINE, r'Microsoft\VCExpress\11.0\Setup\VC\ProductDir'),
    ],
    '10.0': [
        (SCons.Util.HKEY_LOCAL_MACHINE, r'Microsoft\VisualStudio\10.0\Setup\VC\ProductDir'),
    ],
    '10.0Exp': [
        (SCons.Util.HKEY_LOCAL_MACHINE, r'Microsoft\VCExpress\10.0\Setup\VC\ProductDir'),
    ],
    '9.0': [
        (SCons.Util.HKEY_CURRENT_USER, r'Microsoft\DevDiv\VCForPython\9.0\installdir',),
        (SCons.Util.HKEY_LOCAL_MACHINE, r'Microsoft\VisualStudio\9.0\Setup\VC\ProductDir',),
    ],
    '9.0Exp': [
        (SCons.Util.HKEY_LOCAL_MACHINE, r'Microsoft\VCExpress\9.0\Setup\VC\ProductDir'),
    ],
    '8.0': [
        (SCons.Util.HKEY_LOCAL_MACHINE, r'Microsoft\VisualStudio\8.0\Setup\VC\ProductDir'),
    ],
    '8.0Exp': [
        (SCons.Util.HKEY_LOCAL_MACHINE, r'Microsoft\VCExpress\8.0\Setup\VC\ProductDir'),
    ],
    '7.1': [
        (SCons.Util.HKEY_LOCAL_MACHINE, r'Microsoft\VisualStudio\7.1\Setup\VC\ProductDir'),
    ],
    '7.0': [
        (SCons.Util.HKEY_LOCAL_MACHINE, r'Microsoft\VisualStudio\7.0\Setup\VC\ProductDir'),
    ],
    '6.0': [
        (SCons.Util.HKEY_LOCAL_MACHINE, r'Microsoft\VisualStudio\6.0\Setup\Microsoft Visual C++\ProductDir'),
    ]
}


def msvc_version_to_maj_min(msvc_version):
    msvc_version_numeric = get_msvc_version_numeric(msvc_version)

    t = msvc_version_numeric.split(".")
    if not len(t) == 2:
        raise ValueError("Unrecognized version %s (%s)" % (msvc_version,msvc_version_numeric))
    try:
        maj = int(t[0])
        min = int(t[1])
        return maj, min
    except ValueError as e:
        raise ValueError("Unrecognized version %s (%s)" % (msvc_version,msvc_version_numeric))


def is_host_target_supported(host_target, msvc_version):
    """Check if (host, target) pair is supported for a VC version.

    Only checks whether a given version *may* support the given
    (host, target) pair, not that the toolchain is actually on the machine.

    Args:
        host_target: canonalized host-target pair, e.g.
          ("x86", "amd64") for cross compilation from 32- to 64-bit Windows.
        msvc_version: Visual C++ version (major.minor), e.g. "10.0"

    Returns:
        True or False

    """
    # We assume that any Visual Studio version supports x86 as a target
    if host_target[1] != "x86":
        maj, min = msvc_version_to_maj_min(msvc_version)
        if maj < 8:
            return False
    return True


VSWHERE_PATHS = [os.path.join(p,'vswhere.exe') for p in  [
    os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer"),
    os.path.expandvars(r"%ProgramFiles%\Microsoft Visual Studio\Installer"),
    os.path.expandvars(r"%ChocolateyInstall%\bin"),
]]

def msvc_find_vswhere():
    """ Find the location of vswhere """
    # For bug 3333: support default location of vswhere for both
    # 64 and 32 bit windows installs.
    # For bug 3542: also accommodate not being on C: drive.
    # NB: this gets called from testsuite on non-Windows platforms.
    # Whether that makes sense or not, don't break it for those.
    vswhere_path = None
    for pf in VSWHERE_PATHS:
        if os.path.exists(pf):
            vswhere_path = pf
            break

    return vswhere_path

def find_vc_pdir_vswhere(msvc_version, env=None):
    """ Find the MSVC product directory using the vswhere program.

    Args:
        msvc_version: MSVC version to search for
        env: optional to look up VSWHERE variable

    Returns:
        MSVC install dir or None

    Raises:
        UnsupportedVersion: if the version is not known by this file

    """
    try:
        vswhere_version = _VCVER_TO_VSWHERE_VER[msvc_version]
    except KeyError:
        debug("Unknown version of MSVC: %s" % msvc_version)
        raise UnsupportedVersion("Unknown version %s" % msvc_version)

    if env is None or not env.get('VSWHERE'):
        vswhere_path = msvc_find_vswhere()
    else:
        vswhere_path = env.subst('$VSWHERE')

    if vswhere_path is None:
        return None

    debug('VSWHERE: %s' % vswhere_path)
    for vswhere_version_args in vswhere_version:

        vswhere_cmd = [vswhere_path] + vswhere_version_args + ["-property", "installationPath"]

        debug("running: %s" % vswhere_cmd)

        #cp = subprocess.run(vswhere_cmd, capture_output=True)  # 3.7+ only
        cp = subprocess.run(vswhere_cmd, stdout=PIPE, stderr=PIPE)

        if cp.stdout:
            # vswhere could return multiple lines, e.g. if Build Tools
            # and {Community,Professional,Enterprise} are both installed.
            # We could define a way to pick the one we prefer, but since
            # this data is currently only used to make a check for existence,
            # returning the first hit should be good enough.
            lines = cp.stdout.decode("mbcs").splitlines()
            return os.path.join(lines[0], 'VC')
        else:
            # We found vswhere, but no install info available for this version
            pass

    return None


def find_vc_pdir(env, msvc_version):
    """Find the MSVC product directory for the given version.

    Tries to look up the path using a registry key from the table
    _VCVER_TO_PRODUCT_DIR; if there is no key, calls find_vc_pdir_wshere
    for help instead.

    Args:
        msvc_version: str
            msvc version (major.minor, e.g. 10.0)

    Returns:
        str: Path found in registry, or None

    Raises:
        UnsupportedVersion: if the version is not known by this file.
        MissingConfiguration: found version but the directory is missing.

        Both exceptions inherit from VisualCException.

    """
    root = 'Software\\'
    try:
        hkeys = _VCVER_TO_PRODUCT_DIR[msvc_version]
    except KeyError:
        debug("Unknown version of MSVC: %s" % msvc_version)
        raise UnsupportedVersion("Unknown version %s" % msvc_version)

    for hkroot, key in hkeys:
        try:
            comps = None
            if not key:
                comps = find_vc_pdir_vswhere(msvc_version, env)
                if not comps:
                    debug('no VC found for version {}'.format(repr(msvc_version)))
                    raise OSError
                debug('VC found: {}'.format(repr(msvc_version)))
                return comps
            else:
                if common.is_win64():
                    try:
                        # ordinarily at win64, try Wow6432Node first.
                        comps = common.read_reg(root + 'Wow6432Node\\' + key, hkroot)
                    except OSError:
                        # at Microsoft Visual Studio for Python 2.7, value is not in Wow6432Node
                        pass
                if not comps:
                    # not Win64, or Microsoft Visual Studio for Python 2.7
                    comps = common.read_reg(root + key, hkroot)
        except OSError:
            debug('no VC registry key {}'.format(repr(key)))
        else:
            debug('found VC in registry: {}'.format(comps))
            if os.path.exists(comps):
                return comps
            else:
                debug('reg says dir is {}, but it does not exist. (ignoring)'.format(comps))
                raise MissingConfiguration("registry dir {} not found on the filesystem".format(comps))
    return None

def find_batch_file(env,msvc_version,host_arch,target_arch):
    """
    Find the location of the batch script which should set up the compiler
    for any TARGET_ARCH whose compilers were installed by Visual Studio/VCExpress

    In newer (2017+) compilers, make use of the fact there are vcvars
    scripts named with a host_target pair that calls vcvarsall.bat properly,
    so use that and return an indication we don't need the argument
    we would have computed to run vcvarsall.bat.
    """
    pdir = find_vc_pdir(env, msvc_version)
    if pdir is None:
        raise NoVersionFound("No version of Visual Studio found")
    debug('looking in {}'.format(pdir))

    # filter out e.g. "Exp" from the version name
    msvc_ver_numeric = get_msvc_version_numeric(msvc_version)
    use_arg = True
    vernum = float(msvc_ver_numeric)
    if 7 <= vernum < 8:
        pdir = os.path.join(pdir, os.pardir, "Common7", "Tools")
        batfilename = os.path.join(pdir, "vsvars32.bat")
    elif vernum < 7:
        pdir = os.path.join(pdir, "Bin")
        batfilename = os.path.join(pdir, "vcvars32.bat")
    elif 8 <= vernum <= 14:
        batfilename = os.path.join(pdir, "vcvarsall.bat")
    else:  # vernum >= 14.1  VS2017 and above
        batfiledir = os.path.join(pdir, "Auxiliary", "Build")
        targ  = _HOST_TARGET_TO_BAT_ARCH_GT14[(host_arch, target_arch)]
        batfilename = os.path.join(batfiledir, targ)
        use_arg = False

    if not os.path.exists(batfilename):
        debug("Not found: %s" % batfilename)
        batfilename = None

    installed_sdks = get_installed_sdks()
    for _sdk in installed_sdks:
        sdk_bat_file = _sdk.get_sdk_vc_script(host_arch,target_arch)
        if not sdk_bat_file:
            debug("batch file not found:%s" % _sdk)
        else:
            sdk_bat_file_path = os.path.join(pdir,sdk_bat_file)
            if os.path.exists(sdk_bat_file_path):
                debug('sdk_bat_file_path:%s' % sdk_bat_file_path)
                return (batfilename, use_arg, sdk_bat_file_path)

    return (batfilename, use_arg, None)


__INSTALLED_VCS_RUN = None
_VC_TOOLS_VERSION_FILE_PATH = ['Auxiliary', 'Build', 'Microsoft.VCToolsVersion.default.txt']
_VC_TOOLS_VERSION_FILE = os.sep.join(_VC_TOOLS_VERSION_FILE_PATH)

def _check_cl_exists_in_vc_dir(env, vc_dir, msvc_version):
    """Return status of finding a cl.exe to use.

    Locates cl in the vc_dir depending on TARGET_ARCH, HOST_ARCH and the
    msvc version. TARGET_ARCH and HOST_ARCH can be extracted from the
    passed env, unless it is None, in which case the native platform is
    assumed for both host and target.

    Args:
        env: Environment
            a construction environment, usually if this is passed its
            because there is a desired TARGET_ARCH to be used when searching
            for a cl.exe
        vc_dir: str
            the path to the VC dir in the MSVC installation
        msvc_version: str
            msvc version (major.minor, e.g. 10.0)

    Returns:
        bool:

    """

    # determine if there is a specific target platform we want to build for and
    # use that to find a list of valid VCs, default is host platform == target platform
    # and same for if no env is specified to extract target platform from
    if env:
        (host_platform, target_platform, req_target_platform) = get_host_target(env)
    else:
        host_platform = platform.machine().lower()
        target_platform = host_platform

    host_platform = _ARCH_TO_CANONICAL[host_platform]
    target_platform = _ARCH_TO_CANONICAL[target_platform]

    debug('host platform %s, target platform %s for version %s' % (host_platform, target_platform, msvc_version))

    ver_num = float(get_msvc_version_numeric(msvc_version))

    # make sure the cl.exe exists meaning the tool is installed
    if ver_num > 14:
        # 2017 and newer allowed multiple versions of the VC toolset to be
        # installed at the same time. This changes the layout.
        # Just get the default tool version for now
        #TODO: support setting a specific minor VC version
        default_toolset_file = os.path.join(vc_dir, _VC_TOOLS_VERSION_FILE)
        try:
            with open(default_toolset_file) as f:
                vc_specific_version = f.readlines()[0].strip()
        except IOError:
            debug('failed to read ' + default_toolset_file)
            return False
        except IndexError:
            debug('failed to find MSVC version in ' + default_toolset_file)
            return False

        host_trgt_dir = _HOST_TARGET_TO_CL_DIR_GREATER_THAN_14.get((host_platform, target_platform), None)
        if host_trgt_dir is None:
            debug('unsupported host/target platform combo: (%s,%s)'%(host_platform, target_platform))
            return False

        cl_path = os.path.join(vc_dir, 'Tools','MSVC', vc_specific_version, 'bin',  host_trgt_dir[0], host_trgt_dir[1], _CL_EXE_NAME)
        debug('checking for ' + _CL_EXE_NAME + ' at ' + cl_path)
        if os.path.exists(cl_path):
            debug('found ' + _CL_EXE_NAME + '!')
            return True

        elif host_platform == "amd64" and host_trgt_dir[0] == "Hostx64":
            # Special case: fallback to Hostx86 if Hostx64 was tried
            # and failed.  This is because VS 2017 Express running on amd64
            # will look to our probe like the host dir should be Hostx64,
            # but Express uses Hostx86 anyway.
            # We should key this off the "x86_amd64" and related pseudo
            # targets, but we don't see those in this function.
            host_trgt_dir = ("Hostx86", host_trgt_dir[1])
            cl_path = os.path.join(vc_dir, 'Tools','MSVC', vc_specific_version, 'bin',  host_trgt_dir[0], host_trgt_dir[1], _CL_EXE_NAME)
            debug('checking for ' + _CL_EXE_NAME + ' at ' + cl_path)
            if os.path.exists(cl_path):
                debug('found ' + _CL_EXE_NAME + '!')
                return True

    elif 14 >= ver_num >= 8:
        # Set default value to be -1 as "", which is the value for x86/x86,
        # yields true when tested if not host_trgt_dir
        host_trgt_dir = _HOST_TARGET_TO_CL_DIR.get((host_platform, target_platform), None)
        if host_trgt_dir is None:
            debug('unsupported host/target platform combo')
            return False

        cl_path = os.path.join(vc_dir, 'bin',  host_trgt_dir, _CL_EXE_NAME)
        debug('checking for ' + _CL_EXE_NAME + ' at ' + cl_path)

        cl_path_exists = os.path.exists(cl_path)
        if not cl_path_exists and host_platform == 'amd64':
            # older versions of visual studio only had x86 binaries,
            # so if the host platform is amd64, we need to check cross
            # compile options (x86 binary compiles some other target on a 64 bit os)

            # Set default value to be -1 as "" which is the value for x86/x86 yields true when tested
            # if not host_trgt_dir
            host_trgt_dir = _HOST_TARGET_TO_CL_DIR.get(('x86', target_platform), None)
            if host_trgt_dir is None:
                return False

            cl_path = os.path.join(vc_dir, 'bin', host_trgt_dir, _CL_EXE_NAME)
            debug('checking for ' + _CL_EXE_NAME + ' at ' + cl_path)
            cl_path_exists = os.path.exists(cl_path)

        if cl_path_exists:
            debug('found ' + _CL_EXE_NAME + '!')
            return True

    elif 8 > ver_num >= 6:
        # quick check for vc_dir/bin and vc_dir/ before walk
        # need to check root as the walk only considers subdirectories
        for cl_dir in ('bin', ''):
            cl_path = os.path.join(vc_dir, cl_dir, _CL_EXE_NAME)
            if os.path.exists(cl_path):
                debug(_CL_EXE_NAME + ' found %s' % cl_path)
                return True
        # not in bin or root: must be in a subdirectory
        for cl_root, cl_dirs, _ in os.walk(vc_dir):
            for cl_dir in cl_dirs:
                cl_path = os.path.join(cl_root, cl_dir, _CL_EXE_NAME)
                if os.path.exists(cl_path):
                    debug(_CL_EXE_NAME + ' found %s' % cl_path)
                    return True
        return False
    else:
        # version not support return false
        debug('unsupported MSVC version: ' + str(ver_num))

    return False

def get_installed_vcs(env=None):
    global __INSTALLED_VCS_RUN

    if __INSTALLED_VCS_RUN is not None:
        return __INSTALLED_VCS_RUN

    installed_versions = []

    for ver in _VCVER:
        debug('trying to find VC %s' % ver)
        try:
            VC_DIR = find_vc_pdir(env, ver)

            if VC_DIR:
                debug('found VC %s' % ver)
                if _check_cl_exists_in_vc_dir(env, VC_DIR, ver):
                    installed_versions.append(ver)
                else:
                    debug('no compiler found %s' % ver)
            else:
                debug('return None for ver %s' % ver)
        except (MSVCUnsupportedTargetArch, MSVCUnsupportedHostArch):
            # Allow this exception to propagate further as it should cause
            # SCons to exit with an error code
            raise
        except VisualCException as e:
            debug('did not find VC %s: caught exception %s' % (ver, str(e)))

    __INSTALLED_VCS_RUN = installed_versions
    return __INSTALLED_VCS_RUN

def reset_installed_vcs():
    """Make it try again to find VC.  This is just for the tests."""
    global __INSTALLED_VCS_RUN
    __INSTALLED_VCS_RUN = None

# Running these batch files isn't cheap: most of the time spent in
# msvs.generate() is due to vcvars*.bat.  In a build that uses "tools='msvs'"
# in multiple environments, for example:
#    env1 = Environment(tools='msvs')
#    env2 = Environment(tools='msvs')
# we can greatly improve the speed of the second and subsequent Environment
# (or Clone) calls by memoizing the environment variables set by vcvars*.bat.
#
# Updated: by 2018, vcvarsall.bat had gotten so expensive (vs2017 era)
# it was breaking CI builds because the test suite starts scons so many
# times and the existing memo logic only helped with repeated calls
# within the same scons run. Windows builds on the CI system were split
# into chunks to get around single-build time limits.
# With VS2019 it got even slower and an optional persistent cache file
# was introduced. The cache now also stores only the parsed vars,
# not the entire output of running the batch file - saves a bit
# of time not parsing every time.

script_env_cache = None

def script_env(script, args=None):
    global script_env_cache

    if script_env_cache is None:
        script_env_cache = common.read_script_env_cache()
    cache_key = "{}--{}".format(script, args)
    cache_data = script_env_cache.get(cache_key, None)
    if cache_data is None:
        stdout = common.get_output(script, args)

        # Stupid batch files do not set return code: we take a look at the
        # beginning of the output for an error message instead
        olines = stdout.splitlines()
        if olines[0].startswith("The specified configuration type is missing"):
            raise BatchFileExecutionError("\n".join(olines[:2]))

        cache_data = common.parse_output(stdout)
        script_env_cache[cache_key] = cache_data
        # once we updated cache, give a chance to write out if user wanted
        common.write_script_env_cache(script_env_cache)

    return cache_data

def get_default_version(env):
    msvc_version = env.get('MSVC_VERSION')
    msvs_version = env.get('MSVS_VERSION')
    debug('msvc_version:%s msvs_version:%s' % (msvc_version, msvs_version))

    if msvs_version and not msvc_version:
        SCons.Warnings.warn(
                SCons.Warnings.DeprecatedWarning,
                "MSVS_VERSION is deprecated: please use MSVC_VERSION instead ")
        return msvs_version
    elif msvc_version and msvs_version:
        if not msvc_version == msvs_version:
            SCons.Warnings.warn(
                    SCons.Warnings.VisualVersionMismatch,
                    "Requested msvc version (%s) and msvs version (%s) do " \
                    "not match: please use MSVC_VERSION only to request a " \
                    "visual studio version, MSVS_VERSION is deprecated" \
                    % (msvc_version, msvs_version))
        return msvs_version

    if not msvc_version:
        installed_vcs = get_installed_vcs(env)
        debug('installed_vcs:%s' % installed_vcs)
        if not installed_vcs:
            #msg = 'No installed VCs'
            #debug('msv %s' % repr(msg))
            #SCons.Warnings.warn(SCons.Warnings.VisualCMissingWarning, msg)
            debug('No installed VCs')
            return None
        msvc_version = installed_vcs[0]
        debug('using default installed MSVC version %s' % repr(msvc_version))
    else:
        debug('using specified MSVC version %s' % repr(msvc_version))

    return msvc_version

def msvc_setup_env_once(env):
    try:
        has_run  = env["MSVC_SETUP_RUN"]
    except KeyError:
        has_run = False

    if not has_run:
        msvc_setup_env(env)
        env["MSVC_SETUP_RUN"] = True

def msvc_find_valid_batch_script(env, version):
    """Find and execute appropriate batch script to set up build env.

    The MSVC build environment depends heavily on having the shell
    environment set.  SCons does not inherit that, and does not count
    on that being set up correctly anyway, so it tries to find the right
    MSVC batch script, or the right arguments to the generic batch script
    vcvarsall.bat, and run that, so we have a valid environment to build in.
    There are dragons here: the batch scripts don't fail (see comments
    elsewhere), they just leave you with a bad setup, so try hard to
    get it right.
    """

    # Find the host, target, and if present the requested target:
    platforms = get_host_target(env)
    debug("host_platform %s, target_platform %s req_target_platform %s" % platforms)
    host_platform, target_platform, req_target_platform = platforms

    # Most combinations of host + target are straightforward.
    # While all MSVC / Visual Studio tools are pysically 32-bit, they
    # make it look like there are 64-bit tools if the host is 64-bit,
    # so you can invoke the environment batch script to set up to build,
    # say, amd64 host -> x86 target. Express versions are an exception:
    # they always look 32-bit, so the batch scripts with 64-bit
    # host parts are absent. We try to fix that up in a couple of ways.
    # One is here: we make a table of "targets" to try, with the extra
    # targets being tags that tell us to try a different "host" instead
    # of the deduced host.
    try_target_archs = [target_platform]
    if req_target_platform in ('amd64', 'x86_64'):
        try_target_archs.append('x86_amd64')
    elif req_target_platform in ('x86',):
        try_target_archs.append('x86_x86')
    elif req_target_platform in ('arm',):
        try_target_archs.append('x86_arm')
    elif req_target_platform in ('arm64',):
        try_target_archs.append('x86_arm64')
    elif not req_target_platform:
        if target_platform in ('amd64', 'x86_64'):
            try_target_archs.append('x86_amd64')
            # If the user hasn't specifically requested a TARGET_ARCH,
            # and the TARGET_ARCH is amd64 then also try 32 bits
            # if there are no viable 64 bit tools installed
            try_target_archs.append('x86')

    debug("host_platform: %s, try_target_archs: %s"%(host_platform, try_target_archs))

    d = None
    for tp in try_target_archs:
        # Set to current arch.
        env['TARGET_ARCH'] = tp

        debug("trying target_platform:%s" % tp)
        host_target = (host_platform, tp)
        if not is_host_target_supported(host_target, version):
            warn_msg = "host, target = %s not supported for MSVC version %s" % \
                (host_target, version)
            SCons.Warnings.warn(SCons.Warnings.VisualCMissingWarning, warn_msg)
        arg = _HOST_TARGET_ARCH_TO_BAT_ARCH[host_target]

        # Try to locate a batch file for this host/target platform combo
        try:
            (vc_script, use_arg, sdk_script) = find_batch_file(env, version, host_platform, tp)
            debug('vc_script:%s sdk_script:%s'%(vc_script,sdk_script))
        except VisualCException as e:
            msg = str(e)
            debug('Caught exception while looking for batch file (%s)' % msg)
            warn_msg = "VC version %s not installed.  " + \
                       "C/C++ compilers are most likely not set correctly.\n" + \
                       " Installed versions are: %s"
            warn_msg = warn_msg % (version, get_installed_vcs(env))
            SCons.Warnings.warn(SCons.Warnings.VisualCMissingWarning, warn_msg)
            continue

        # Try to use the located batch file for this host/target platform combo
        debug('use_script 2 %s, args:%s' % (repr(vc_script), arg))
        found = None
        if vc_script:
            if not use_arg:
                arg = ''  # bat file will supply platform type
            # Get just version numbers
            maj, min = msvc_version_to_maj_min(version)
            # VS2015+
            if maj >= 14:
                if env.get('MSVC_UWP_APP') == '1':
                    # Initialize environment variables with store/UWP paths
                    arg = (arg + ' store').lstrip()

            try:
                d = script_env(vc_script, args=arg)
                found = vc_script
            except BatchFileExecutionError as e:
                debug('use_script 3: failed running VC script %s: %s: Error:%s'%(repr(vc_script),arg,e))
                vc_script=None
                continue
        if not vc_script and sdk_script:
            debug('use_script 4: trying sdk script: %s' % sdk_script)
            try:
                d = script_env(sdk_script)
                found = sdk_script
            except BatchFileExecutionError as e:
                debug('use_script 5: failed running SDK script %s: Error:%s'%(repr(sdk_script), e))
                continue
        elif not vc_script and not sdk_script:
            debug('use_script 6: Neither VC script nor SDK script found')
            continue

        debug("Found a working script/target: %s/%s"%(repr(found),arg))
        break # We've found a working target_platform, so stop looking

    # If we cannot find a viable installed compiler, reset the TARGET_ARCH
    # To it's initial value
    if not d:
        env['TARGET_ARCH']=req_target_platform

    return d


def msvc_setup_env(env):
    debug('called')
    version = get_default_version(env)
    if version is None:
        warn_msg = "No version of Visual Studio compiler found - C/C++ " \
                   "compilers most likely not set correctly"

        # Nuitka: Useless warning for us.
        # SCons.Warnings.warn(SCons.Warnings.VisualCMissingWarning, warn_msg)
        return None

    # XXX: we set-up both MSVS version for backward
    # compatibility with the msvs tool
    env['MSVC_VERSION'] = version
    env['MSVS_VERSION'] = version
    env['MSVS'] = {}


    use_script = env.get('MSVC_USE_SCRIPT', True)
    if SCons.Util.is_String(use_script):
        debug('use_script 1 %s' % repr(use_script))
        d = script_env(use_script)
    elif use_script:
        d = msvc_find_valid_batch_script(env,version)
        debug('use_script 2 %s' % d)
        if not d:
            return d
    else:
        debug('MSVC_USE_SCRIPT set to False')
        warn_msg = "MSVC_USE_SCRIPT set to False, assuming environment " \
                   "set correctly."
        # Nuitka: We use this on purpose.
        # SCons.Warnings.warn(SCons.Warnings.VisualCMissingWarning, warn_msg)
        return None

    for k, v in d.items():
        # Nuitka: Make the Windows SDK version visible in environment.
        if k == "WindowsSDKVersion":
            # Always just a single version if any.
            if len(v) == 1:
                env["WindowsSDKVersion"] = v[0].rstrip('\\')
            elif len(v) == 0:
                env["WindowsSDKVersion"] = None
            else:
                assert False, v

            continue

        env.PrependENVPath(k, v, delete_existing=True)
        debug("env['ENV']['%s'] = %s" % (k, env['ENV'][k]))

    # final check to issue a warning if the compiler is not present
    if not find_program_path(env, 'cl'):
        debug("did not find " + _CL_EXE_NAME)
        if CONFIG_CACHE:
            propose = "SCONS_CACHE_MSVC_CONFIG caching enabled, remove cache file {} if out of date.".format(CONFIG_CACHE)
        else:
            propose = "It may need to be installed separately with Visual Studio."
        warn_msg = "Could not find MSVC compiler 'cl'. {}".format(propose)
        SCons.Warnings.warn(SCons.Warnings.VisualCMissingWarning, warn_msg)

def msvc_exists(env=None, version=None):
    vcs = get_installed_vcs(env)
    if version is None:
        return len(vcs) > 0
    return version in vcs
