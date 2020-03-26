"""gettext tool
"""


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

__revision__ = "src/engine/SCons/Tool/gettext_tool.py bee7caf9defd6e108fc2998a2520ddb36a967691 2019-12-17 02:07:09 bdeegan"

#############################################################################
def generate(env,**kw):
  import sys
  import os
  import SCons.Tool
  from SCons.Platform.mingw import MINGW_DEFAULT_PATHS
  from SCons.Platform.cygwin import CYGWIN_DEFAULT_PATHS

  from SCons.Tool.GettextCommon \
    import  _translate, tool_list
  for t in tool_list(env['PLATFORM'], env):
    if sys.platform == 'win32':
        tool = SCons.Tool.find_program_path(env, t, default_paths=MINGW_DEFAULT_PATHS + CYGWIN_DEFAULT_PATHS )
        if tool:
            tool_bin_dir = os.path.dirname(tool)
            env.AppendENVPath('PATH', tool_bin_dir)
        else:
            SCons.Warnings.Warning(t + ' tool requested, but binary not found in ENV PATH')
    env.Tool(t)
  env.AddMethod(_translate, 'Translate')
#############################################################################

#############################################################################
def exists(env):
  from SCons.Tool.GettextCommon \
  import _xgettext_exists, _msginit_exists, \
         _msgmerge_exists, _msgfmt_exists
  try:
    return _xgettext_exists(env) and _msginit_exists(env) \
       and _msgmerge_exists(env) and _msgfmt_exists(env)
  except:
    return False
#############################################################################
