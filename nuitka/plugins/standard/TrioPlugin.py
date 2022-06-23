#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
"""Trio plugin module."""

from nuitka.plugins.PluginBase import NuitkaPluginBase

_trio_patches = {
    "trio._core._ki": (
        """\
enable_ki_protection = _ki_protection_decorator(True)  # type: Callable[[F], F]
enable_ki_protection.__name__ = "enable_ki_protection"

disable_ki_protection = _ki_protection_decorator(False)  # type: Callable[[F], F]
disable_ki_protection.__name__ = "disable_ki_protection"
""",
        """\
def enable_ki_protection(fn):
    return fn

def disable_ki_protection(fn):
    return fn
""",
    ),
    "trio._core._run": (
        "coro.cr_frame.f_locals.setdefault(LOCALS_KEY_KI_PROTECTION_ENABLED, system_task)",
        "# coro.cr_frame.f_locals.setdefault(LOCALS_KEY_KI_PROTECTION_ENABLED, system_task)",
    ),
}


class NuitkaPluginTrio(NuitkaPluginBase):
    """Plugin for compatibility with Trio.

    The only incompatibility in Trio is the way it handles KeyboardInterrupt exceptions (ctrl+C):

    https://github.com/Nuitka/Nuitka/issues/561
    https://github.com/python-trio/trio/issues/1752

    It does this to ensure that Trio's internal data structures stay consistent and that the
    `finally` blocks in suspended coroutines are all run:

    https://vorpus.org/blog/control-c-handling-in-python-and-trio/

    So, be warned, when this plugin is enabled, your Trio code may not behave as expected when the
    user hits CTRL+C. One option to cope with this is to run your Trio code in a separate thread,
    listen for it in the main thread (with a try/except block), then notify the Trio thread to
    shutdown (e.g. with `trio_token.run_sync_soon(cancel_scope.cancel())`).

    """

    plugin_name = "trio"
    plugin_desc = "Required for Trio package"

    def __init__(self):
        self.shown_warning = False

    def onModuleSourceCode(self, module_name, source_code):
        if module_name not in _trio_patches:
            return

        if not self.shown_warning:
            self.info("Disabling careful handling of KeyboardInterrupt in Trio")
            self.shown_warning = True

        code_before, code_after = _trio_patches[module_name]

        if code_before not in source_code:
            self.sysexit(
                "Could not find code to patch in " + module_name + ":\n" + code_before
            )

        return source_code.replace(code_before, code_after)
