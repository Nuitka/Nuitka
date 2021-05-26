import os
import sys

from nuitka import Options
from nuitka.plugins.PluginBase import NuitkaPluginBase


class JsonschemaPlugin(NuitkaPluginBase):

    plugin_name = "jsonschema"
    plugin_desc = "Handle metadata version"

    def onModuleSourceCode(self, module_name, source_code):
        """Hardcode the package version"""
        if module_name != "jsonschema":
            return source_code
        try:
            from importlib import metadata
        except ImportError:  # for Python<3.8
            import importlib_metadata as metadata
        version = f'"{metadata.version("jsonschema")}"'
        source_code = source_code.replace('metadata.version("jsonschema")', version)
        return source_code
