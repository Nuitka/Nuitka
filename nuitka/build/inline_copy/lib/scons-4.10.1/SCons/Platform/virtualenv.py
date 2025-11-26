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

"""Platform support for a Python virtualenv.

This is support code, not a loadable Platform module.
"""

from __future__ import annotations

import os
import sys
import SCons.Util


virtualenv_enabled_by_default = False


def _enable_virtualenv_default():
    return SCons.Util.get_os_env_bool('SCONS_ENABLE_VIRTUALENV', virtualenv_enabled_by_default)


def _ignore_virtualenv_default():
    return SCons.Util.get_os_env_bool('SCONS_IGNORE_VIRTUALENV', False)


enable_virtualenv = _enable_virtualenv_default()
ignore_virtualenv = _ignore_virtualenv_default()

# Variables to export:
# - Python docs:
#   When a virtual environment has been activated, the VIRTUAL_ENV environment
#   variable is set to the path of the environment.  Since explicitly
#   activating a virtual environment is not required to use it, VIRTUAL_ENV
#   cannot be relied upon to determine whether a virtual environment is being
#   used.
# - pipenv: shell sets PIPENV_ACTIVE, cannot find it documented.
# Any others we should include?
VIRTUALENV_VARIABLES = ['VIRTUAL_ENV', 'PIPENV_ACTIVE']


def _running_in_virtualenv():
    """Check whether scons is running in a virtualenv."""
    # TODO: the virtualenv command used to inject a sys.real_prefix before
    #   Python started officially tracking virtualenvs with the venv module.
    #   All Pythons since 3.3 use sys.base_prefix for tracking (PEP 405);
    #   virtualenv has retired their old behavior and now only makes
    #   venv-style virtualenvs. We're now using the detection suggested in
    #   PEP 668, and should be able to drop the real_prefix check soon.
    return sys.base_prefix != sys.prefix or hasattr(sys, 'real_prefix')


def _is_path_in(path, base):
    """Check if *path* is located under the *base* directory."""
    if not path or not base:  # empty path or base are possible
        return False
    rp = os.path.relpath(path, base)
    return (not rp.startswith(os.path.pardir)) and (not rp == os.path.curdir)


def _inject_venv_variables(env):
    """Copy any set virtualenv variables from ``os.environ`` to *env*."""
    if 'ENV' not in env:
        env['ENV'] = {}
    ENV = env['ENV']
    for name in VIRTUALENV_VARIABLES:
        try:
            ENV[name] = os.environ[name]
        except KeyError:
            pass

def _inject_venv_path(env, path_list=None):
    """Insert virtualenv-related paths from ``os.environe`` to *env*."""
    if path_list is None:
        path_list = os.getenv('PATH')
    env.PrependENVPath('PATH', select_paths_in_venv(path_list))


def select_paths_in_venv(path_list):
    """Filter *path_list*, returning values under the virtualenv."""
    if SCons.Util.is_String(path_list):
        path_list = path_list.split(os.path.pathsep)
    return [path for path in path_list if IsInVirtualenv(path)]


def ImportVirtualenv(env):
    """Add virtualenv information to *env*."""
    _inject_venv_variables(env)
    _inject_venv_path(env)


def Virtualenv():
    """Return whether operating in a virtualenv.

    Returns the path to the virtualenv home if scons is executing
    within a virtualenv, else and empty string.
    """
    if _running_in_virtualenv():
        return sys.prefix
    return ""


def IsInVirtualenv(path):
    """Check whether *path* is under the virtualenv's directory.

    Returns ``False`` if not using a virtualenv.
    """
    return _is_path_in(path, Virtualenv())


# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
