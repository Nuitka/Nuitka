"""
Common helper functions for working with the Microsoft tool chain.
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

import copy
import json
import os
import re
import subprocess
import sys

import SCons.Util

# SCONS_MSCOMMON_DEBUG is internal-use so undocumented:
# set to '-' to print to console, else set to filename to log to
LOGFILE = os.environ.get('SCONS_MSCOMMON_DEBUG')
if LOGFILE == '-':
    def debug(message):
        print(message)
elif LOGFILE:
    import logging
    modulelist = (
        # root module and parent/root module
        'MSCommon', 'Tool',
        # python library and below: correct iff scons does not have a lib folder
        'lib',
        # scons modules
        'SCons', 'test', 'scons'
    )
    def get_relative_filename(filename, module_list):
        if not filename:
            return filename
        for module in module_list:
            try:
                ind = filename.rindex(module)
                return filename[ind:]
            except ValueError:
                pass
        return filename
    class _Debug_Filter(logging.Filter):
        # custom filter for module relative filename
        def filter(self, record):
            relfilename = get_relative_filename(record.pathname, modulelist)
            relfilename = relfilename.replace('\\', '/')
            record.relfilename = relfilename
            return True
    logging.basicConfig(
        # This looks like:
        #   00109ms:MSCommon/vc.py:find_vc_pdir#447:
        format=(
            '%(relativeCreated)05dms'
            ':%(relfilename)s'
            ':%(funcName)s'
            '#%(lineno)s'
            ':%(message)s: '
        ),
        filename=LOGFILE,
        level=logging.DEBUG)
    logger = logging.getLogger(name=__name__)
    logger.addFilter(_Debug_Filter())
    debug = logger.debug
else:
    def debug(x): return None


# SCONS_CACHE_MSVC_CONFIG is public, and is documented.
CONFIG_CACHE = os.environ.get('SCONS_CACHE_MSVC_CONFIG')
if CONFIG_CACHE in ('1', 'true', 'True'):
    CONFIG_CACHE = os.path.join(os.path.expanduser('~'), '.scons_msvc_cache')


def read_script_env_cache():
    """ fetch cached msvc env vars if requested, else return empty dict """
    envcache = {}
    if CONFIG_CACHE:
        try:
            with open(CONFIG_CACHE, 'r') as f:
                envcache = json.load(f)
        except FileNotFoundError:
            # don't fail if no cache file, just proceed without it
            pass
    return envcache


def write_script_env_cache(cache):
    """ write out cache of msvc env vars if requested """
    if CONFIG_CACHE:
        try:
            with open(CONFIG_CACHE, 'w') as f:
                json.dump(cache, f, indent=2)
        except TypeError:
            # data can't serialize to json, don't leave partial file
            os.remove(CONFIG_CACHE)
        except IOError:
            # can't write the file, just skip
            pass


_is_win64 = None


def is_win64():
    """Return true if running on windows 64 bits.

    Works whether python itself runs in 64 bits or 32 bits."""
    # Unfortunately, python does not provide a useful way to determine
    # if the underlying Windows OS is 32-bit or 64-bit.  Worse, whether
    # the Python itself is 32-bit or 64-bit affects what it returns,
    # so nothing in sys.* or os.* help.

    # Apparently the best solution is to use env vars that Windows
    # sets.  If PROCESSOR_ARCHITECTURE is not x86, then the python
    # process is running in 64 bit mode (on a 64-bit OS, 64-bit
    # hardware, obviously).
    # If this python is 32-bit but the OS is 64, Windows will set
    # ProgramW6432 and PROCESSOR_ARCHITEW6432 to non-null.
    # (Checking for HKLM\Software\Wow6432Node in the registry doesn't
    # work, because some 32-bit installers create it.)
    global _is_win64
    if _is_win64 is None:
        # I structured these tests to make it easy to add new ones or
        # add exceptions in the future, because this is a bit fragile.
        _is_win64 = False
        if os.environ.get('PROCESSOR_ARCHITECTURE', 'x86') != 'x86':
            _is_win64 = True
        if os.environ.get('PROCESSOR_ARCHITEW6432'):
            _is_win64 = True
        if os.environ.get('ProgramW6432'):
            _is_win64 = True
    return _is_win64


def read_reg(value, hkroot=SCons.Util.HKEY_LOCAL_MACHINE):
    return SCons.Util.RegGetValue(hkroot, value)[0]


def has_reg(value):
    """Return True if the given key exists in HKEY_LOCAL_MACHINE, False
    otherwise."""
    try:
        SCons.Util.RegOpenKeyEx(SCons.Util.HKEY_LOCAL_MACHINE, value)
        ret = True
    except OSError:
        ret = False
    return ret

# Functions for fetching environment variable settings from batch files.


def normalize_env(env, keys, force=False):
    """Given a dictionary representing a shell environment, add the variables
    from os.environ needed for the processing of .bat files; the keys are
    controlled by the keys argument.

    It also makes sure the environment values are correctly encoded.

    If force=True, then all of the key values that exist are copied
    into the returned dictionary.  If force=false, values are only
    copied if the key does not already exist in the copied dictionary.

    Note: the environment is copied."""
    normenv = {}
    if env:
        for k, v in env.items():
            normenv[k] = copy.deepcopy(v)

        for k in keys:
            if k in os.environ and (force or k not in normenv):
                normenv[k] = os.environ[k]

    # add some things to PATH to prevent problems:
    # Shouldn't be necessary to add system32, since the default environment
    # should include it, but keep this here to be safe (needed for reg.exe)
    sys32_dir = os.path.join(
        os.environ.get("SystemRoot", os.environ.get("windir", r"C:\Windows")), "System32"
)
    if sys32_dir not in normenv["PATH"]:
        normenv["PATH"] = normenv["PATH"] + os.pathsep + sys32_dir

    # Without Wbem in PATH, vcvarsall.bat has a "'wmic' is not recognized"
    # error starting with Visual Studio 2017, although the script still
    # seems to work anyway.
    sys32_wbem_dir = os.path.join(sys32_dir, 'Wbem')
    if sys32_wbem_dir not in normenv['PATH']:
        normenv['PATH'] = normenv['PATH'] + os.pathsep + sys32_wbem_dir

    # Without Powershell in PATH, an internal call to a telemetry
    # function (starting with a VS2019 update) can fail
    # Note can also set VSCMD_SKIP_SENDTELEMETRY to avoid this.
    sys32_ps_dir = os.path.join(sys32_dir, r'WindowsPowerShell\v1.0')
    if sys32_ps_dir not in normenv['PATH']:
        normenv['PATH'] = normenv['PATH'] + os.pathsep + sys32_ps_dir

    debug("PATH: %s" % normenv['PATH'])
    return normenv


def get_output(vcbat, args=None, env=None):
    """Parse the output of given bat file, with given args."""

    if env is None:
        # Create a blank environment, for use in launching the tools
        env = SCons.Environment.Environment(tools=[])

    # TODO:  Hard-coded list of the variables that (may) need to be
    # imported from os.environ[] for the chain of development batch
    # files to execute correctly. One call to vcvars*.bat may
    # end up running a dozen or more scripts, changes not only with
    # each release but with what is installed at the time. We think
    # in modern installations most are set along the way and don't
    # need to be picked from the env, but include these for safety's sake.
    # Any VSCMD variables definitely are picked from the env and
    # control execution in interesting ways.
    # Note these really should be unified - either controlled by vs.py,
    # or synced with the the common_tools_var # settings in vs.py.
    vs_vc_vars = [
        'COMSPEC',  # path to "shell"
        'VS170COMNTOOLS',  # path to common tools for given version
        'VS160COMNTOOLS',
        'VS150COMNTOOLS',
        'VS140COMNTOOLS',
        'VS120COMNTOOLS',
        'VS110COMNTOOLS',
        'VS100COMNTOOLS',
        'VS90COMNTOOLS',
        'VS80COMNTOOLS',
        'VS71COMNTOOLS',
        'VS70COMNTOOLS',
        'VS60COMNTOOLS',
        'VSCMD_DEBUG',   # enable logging and other debug aids
        'VSCMD_SKIP_SENDTELEMETRY',
    ]
    env['ENV'] = normalize_env(env['ENV'], vs_vc_vars, force=False)

    if args:
        debug("Calling '%s %s'" % (vcbat, args))
        popen = SCons.Action._subproc(env,
                                      '"%s" %s & set' % (vcbat, args),
                                      stdin='devnull',
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
    else:
        debug("Calling '%s'" % vcbat)
        popen = SCons.Action._subproc(env,
                                      '"%s" & set' % vcbat,
                                      stdin='devnull',
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)

    # Use the .stdout and .stderr attributes directly because the
    # .communicate() method uses the threading module on Windows
    # and won't work under Pythons not built with threading.
    with popen.stdout:
        stdout = popen.stdout.read()
    with popen.stderr:
        stderr = popen.stderr.read()

    # Extra debug logic, uncomment if necessary
    # debug('stdout:%s' % stdout)
    # debug('stderr:%s' % stderr)

    # Ongoing problems getting non-corrupted text led to this
    # changing to "oem" from "mbcs" - the scripts run presumably
    # attached to a console, so some particular rules apply.
    # Unfortunately, "oem" not defined in Python 3.5, so get another way
    if sys.version_info.major == 3 and sys.version_info.minor < 6:
        from ctypes import windll

        OEM = "cp{}".format(windll.kernel32.GetConsoleOutputCP())
    else:
        OEM = "oem"
    if stderr:
        # TODO: find something better to do with stderr;
        # this at least prevents errors from getting swallowed.
        sys.stderr.write(stderr.decode(OEM))
    if popen.wait() != 0:
        raise IOError(stderr.decode(OEM))

    return stdout.decode(OEM)


KEEPLIST = (
    "INCLUDE",
    "LIB",
    "LIBPATH",
    "PATH",
    "VSCMD_ARG_app_plat",
    "VCINSTALLDIR",  # needed by clang -VS 2017 and newer
    "VCToolsInstallDir",  # needed by clang - VS 2015 and older
)
# Nuitka: Keep the Windows SDK version too
KEEPLIST += ("WindowsSDKVersion",)


def parse_output(output, keep=KEEPLIST):
    """
    Parse output from running visual c++/studios vcvarsall.bat and running set
    To capture the values listed in keep
    """

    # dkeep is a dict associating key: path_list, where key is one item from
    # keep, and path_list the associated list of paths
    dkeep = dict([(i, []) for i in keep])

    # rdk will  keep the regex to match the .bat file output line starts
    rdk = {}
    for i in keep:
        rdk[i] = re.compile('%s=(.*)' % i, re.I)

    def add_env(rmatch, key, dkeep=dkeep):
        path_list = rmatch.group(1).split(os.pathsep)
        for path in path_list:
            # Do not add empty paths (when a var ends with ;)
            if path:
                # XXX: For some reason, VC98 .bat file adds "" around the PATH
                # values, and it screws up the environment later, so we strip
                # it.
                path = path.strip('"')
                dkeep[key].append(str(path))

    for line in output.splitlines():
        for k, value in rdk.items():
            match = value.match(line)
            if match:
                add_env(match, k)

    return dkeep

def get_pch_node(env, target, source):
    """
    Get the actual PCH file node
    """
    pch_subst = env.get('PCH', False) and env.subst('$PCH',target=target, source=source, conv=lambda x:x)

    if not pch_subst:
        return ""

    if SCons.Util.is_String(pch_subst):
        pch_subst = target[0].dir.File(pch_subst)

    return pch_subst


# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
