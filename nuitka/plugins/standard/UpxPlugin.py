#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""UPX plugin. """

import os

from nuitka.Options import isOnefileMode, shallNotCompressOnefile
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.AppDirs import getCacheDir
from nuitka.utils.Execution import executeToolChecked, getExecutablePath
from nuitka.utils.FileOperations import copyFile, getFileContentsHash, makePath
from nuitka.utils.Hashing import Hash
from nuitka.utils.Utils import isLinux


class NuitkaPluginUpx(NuitkaPluginBase):
    """This class represents the main logic of the UPX plugin.

    This is a plugin that removes useless stuff from DLLs and compresses the
    code at the cost of run time increases.

    """

    plugin_name = "upx"  # Nuitka knows us by this name
    plugin_desc = "Compress created binaries with UPX automatically."
    plugin_category = "integration"

    def __init__(self, upx_path, upx_nocache):
        self.upx_binary = getExecutablePath("upx", upx_path)
        self.upx_binary_hash = None
        self.upx_nocache = upx_nocache

    def onCompilationStartChecks(self):
        if self.upx_binary is None:
            self.sysexit(
                """\
No UPX binary found, please use '--upx-binary' option to specify it."""
            )

        if isOnefileMode and not shallNotCompressOnefile() and not isLinux():
            self.warning(
                """\
For best results, disable onefile compression with '--onefile-no-compression' \
as double compression going to give larger and slower results."""
            )

    @classmethod
    def addPluginCommandLineOptions(cls, group):
        group.add_option(
            "--upx-binary",
            action="store",
            dest="upx_path",
            default=None,
            help="""\
The UPX binary to use or the directory it lives in, by default `upx` from PATH is used.""",
        )
        group.add_option(
            "--upx-disable-cache",
            action="store_true",
            dest="upx_nocache",
            default=False,
            help="""\
Do not cache UPX compression result, by default DLLs are cached, exe files are not.""",
        )

    def _filterUpxError(self, stderr, filename):
        new_result = None

        for candidate in (
            b"NotCompressibleException",
            b"CantPackException",
            b"AlreadyPackedException",
        ):
            if candidate in stderr:
                if candidate == b"NotCompressibleException":
                    self.warning("File %s is not compressible." % filename)

                stderr = b""
                new_result = 0

        return new_result, stderr

    def _compressFile(self, filename, use_cache):
        upx_options = ["-q", "--no-progress", "--best", "--lzma"]

        # spell-checker: ignore vcruntime140
        if os.path.basename(filename).startswith("vcruntime140"):
            return

        if use_cache:
            if self.upx_binary_hash is None:
                self.upx_binary_hash = getFileContentsHash(
                    self.upx_binary, as_string=False
                )

            upx_hash = Hash()
            upx_hash.updateFromBytes(self.upx_binary_hash)
            upx_hash.updateFromValues(*upx_options)
            upx_hash.updateFromFile(filename)

            # TODO: Repeating pattern
            upx_cache_dir = getCacheDir("upx")
            makePath(upx_cache_dir)

            upx_cache_filename = os.path.join(
                upx_cache_dir, upx_hash.asHexDigest() + ".bin"
            )

            if os.path.exists(upx_cache_filename):
                copyFile(upx_cache_filename, filename)
                return

        if use_cache:
            self.info(
                "Uncached file, compressing '%s' may take a while."
                % os.path.basename(filename)
            )
        else:
            self.info("Compressing '%s'." % filename)

        command = [self.upx_binary] + upx_options + [filename]

        executeToolChecked(
            logger=self,
            command=command,
            absence_message="UPX not found",
            stderr_filter=self._filterUpxError,
            context={"filename": filename},
        )

        if use_cache:
            copyFile(filename, upx_cache_filename)

    def onCopiedDLL(self, dll_filename):
        if not isOnefileMode():
            self._compressFile(filename=dll_filename, use_cache=not self.upx_nocache)

    # Cannot compress after payload has been added for onefile on Linux,
    # so have a dedicated point for that.
    def onBootstrapBinary(self, filename):
        if isLinux():
            self._compressFile(filename=filename, use_cache=False)

    def onFinalResult(self, filename):
        if not isLinux() or not isOnefileMode():
            self._compressFile(filename=filename, use_cache=False)


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
