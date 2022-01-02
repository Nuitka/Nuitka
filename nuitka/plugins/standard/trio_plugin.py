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
    user hits ctrl+C. One option to cope with this is to run your Trio code in a separate thread,
    listen for it in the main thread (with a try/except block), then notify the Trio thread to
    shutdown (e.g. with `trio_token.run_sync_soon(cancel_scope.cancel())`).

    """

    plugin_name = "trio"
    plugin_desc = "Required for Trio package (disables extra care of KeyboardInterrupt)"

    def __init__(self):
        self.shown_warning = False

    def onModuleSourceCode(self, module_name, source_code):
        if module_name not in _trio_patches:
            return
        if not self.shown_warning:
            self.warning("Disabling careful handling of KeyboardInterrupt in Trio")
            self.shown_warning = True
        code_before, code_after = _trio_patches[module_name]
        if not code_before in source_code:
            self.sysexit(
                "Could not find code to patch in " + module_name + ":\n" + code_before
            )
        return source_code.replace(code_before, code_after)
