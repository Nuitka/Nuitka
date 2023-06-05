#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Standard plug-in to tell Nuitka about implicit imports.

When C extension modules import other modules, we cannot see this and need to
be told that. This encodes the knowledge we have for various modules. Feel free
to add to this and submit patches to make it more complete.
"""

import fnmatch
import os

from nuitka.__past__ import iter_modules
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.ModuleNames import ModuleName
from nuitka.utils.Utils import isMacOS, isWin32Windows
from nuitka.utils.Yaml import getYamlPackageConfiguration


class NuitkaPluginImplicitImports(NuitkaPluginBase):
    plugin_name = "implicit-imports"

    plugin_desc = (
        "Provide implicit imports of package as per package configuration files."
    )

    def __init__(self):
        self.config = getYamlPackageConfiguration()

    @staticmethod
    def isAlwaysEnabled():
        return True

    def _resolveModulePattern(self, pattern):
        parts = pattern.split(".")

        current = None

        for count, part in enumerate(parts):
            if not part:
                self.sysexit(
                    "Error, invalid pattern with empty parts used '%s'." % pattern
                )

            # TODO: Checking for shell pattern should be done in more places and shared code.
            if "?" in part or "*" in part or "[" in part:
                if current is None:
                    self.sysexit(
                        "Error, cannot use pattern for first part '%s'." % pattern
                    )

                module_filename = self.locateModule(
                    module_name=ModuleName(current),
                )

                for sub_module in iter_modules([module_filename]):
                    if not fnmatch.fnmatch(sub_module.name, part):
                        continue

                    if count == len(parts) - 1:
                        yield current.getChildNamed(sub_module.name)
                    else:
                        child_name = current.getChildNamed(sub_module.name).asString()

                        for value in self._resolveModulePattern(
                            child_name + "." + ".".join(parts[count + 1 :])
                        ):
                            yield value

                return
            else:
                if current is None:
                    current = ModuleName(part)
                else:
                    current = current.getChildNamed(part)

        yield current

    def _handleImplicitImportsConfig(self, module, config):
        full_name = module.getFullName()

        for dependency in config.get("depends", ()):
            if dependency.startswith("."):
                if (
                    module.isUncompiledPythonPackage()
                    or module.isCompiledPythonPackage()
                ):
                    dependency = full_name.getChildNamed(dependency[1:]).asString()
                elif full_name.getPackageName() is None:
                    # Not a package, potentially a naming conflict, when
                    # compiling with "--module" something that matches a PyPI
                    # name.
                    continue
                else:
                    dependency = full_name.getSiblingNamed(dependency[1:]).asString()

            if "*" in dependency or "?" in dependency:
                for resolved in self._resolveModulePattern(dependency):
                    yield resolved
            else:
                yield dependency

    def _getImportsByFullname(self, module, full_name):
        """Provides names of modules to imported implicitly."""
        # Many variables, branches, due to the many cases, pylint: disable=too-many-branches,too-many-statements

        # Checking for config, but also allowing fall through.
        for entry in self.config.get(full_name, section="implicit-imports"):
            if self.evaluateCondition(
                full_name=full_name, condition=entry.get("when", "True")
            ):
                for dependency in self._handleImplicitImportsConfig(
                    config=entry, module=module
                ):
                    yield dependency

        # Support for both pycryotodome (module name Crypto) and pycyptodomex (module name Cryptodome)
        if full_name.hasOneOfNamespaces("Crypto", "Cryptodome"):
            crypto_module_name = full_name.getTopLevelPackageName()

            if full_name == crypto_module_name + ".Cipher._mode_ofb":
                yield crypto_module_name + ".Cipher._raw_ofb"

            elif full_name == crypto_module_name + ".Cipher.CAST":
                yield crypto_module_name + ".Cipher._raw_cast"

            elif full_name == crypto_module_name + ".Cipher.DES3":
                yield crypto_module_name + ".Cipher._raw_des3"

            elif full_name == crypto_module_name + ".Cipher.DES":
                yield crypto_module_name + ".Cipher._raw_des"

            elif full_name == crypto_module_name + ".Cipher._mode_ecb":
                yield crypto_module_name + ".Cipher._raw_ecb"

            elif full_name == crypto_module_name + ".Cipher.AES":
                yield crypto_module_name + ".Cipher._raw_aes"
                yield crypto_module_name + ".Cipher._raw_aesni"
                yield crypto_module_name + ".Util._cpuid"

            elif full_name == crypto_module_name + ".Cipher._mode_cfb":
                yield crypto_module_name + ".Cipher._raw_cfb"

            elif full_name == crypto_module_name + ".Cipher.ARC2":
                yield crypto_module_name + ".Cipher._raw_arc2"

            elif full_name == crypto_module_name + ".Cipher.DES3":
                yield crypto_module_name + ".Cipher._raw_des3"

            elif full_name == crypto_module_name + ".Cipher._mode_ocb":
                yield crypto_module_name + ".Cipher._raw_ocb"

            elif full_name == crypto_module_name + ".Cipher._EKSBlowfish":
                yield crypto_module_name + ".Cipher._raw_eksblowfish"

            elif full_name == crypto_module_name + ".Cipher.Blowfish":
                yield crypto_module_name + ".Cipher._raw_blowfish"

            elif full_name == crypto_module_name + ".Cipher._mode_ctr":
                yield crypto_module_name + ".Cipher._raw_ctr"

            elif full_name == crypto_module_name + ".Cipher._mode_cbc":
                yield crypto_module_name + ".Cipher._raw_cbc"

            elif full_name == crypto_module_name + ".Util.strxor":
                yield crypto_module_name + ".Util._strxor"

            elif full_name == crypto_module_name + ".Util._cpu_features":
                yield crypto_module_name + ".Util._cpuid_c"

            elif full_name == crypto_module_name + ".Hash.BLAKE2s":
                yield crypto_module_name + ".Hash._BLAKE2s"

            elif full_name == crypto_module_name + ".Hash.BLAKE2b":
                yield crypto_module_name + ".Hash._BLAKE2b"

            elif full_name == crypto_module_name + ".Hash.SHA1":
                yield crypto_module_name + ".Hash._SHA1"

            elif full_name == crypto_module_name + ".Hash.SHA224":
                yield crypto_module_name + ".Hash._SHA224"

            elif full_name == crypto_module_name + ".Hash.SHA256":
                yield crypto_module_name + ".Hash._SHA256"

            elif full_name == crypto_module_name + ".Hash.SHA384":
                yield crypto_module_name + ".Hash._SHA384"

            elif full_name == crypto_module_name + ".Hash.SHA512":
                yield crypto_module_name + ".Hash._SHA512"

            elif full_name == crypto_module_name + ".Hash.MD2":
                yield crypto_module_name + ".Hash._MD2"

            elif full_name == crypto_module_name + ".Hash.MD4":
                yield crypto_module_name + ".Hash._MD4"

            elif full_name == crypto_module_name + ".Hash.MD5":
                yield crypto_module_name + ".Hash._MD5"

            elif full_name == crypto_module_name + ".Hash.keccak":
                yield crypto_module_name + ".Hash._keccak"

            elif full_name == crypto_module_name + ".Hash.RIPEMD160":
                yield crypto_module_name + ".Hash._RIPEMD160"

            elif full_name == crypto_module_name + ".Hash.Poly1305":
                yield crypto_module_name + ".Hash._poly1305"

            elif full_name == crypto_module_name + ".Protocol.KDF":
                yield crypto_module_name + ".Cipher._Salsa20"
                yield crypto_module_name + ".Protocol._scrypt"

            elif full_name == crypto_module_name + ".Cipher._mode_gcm":
                yield crypto_module_name + ".Hash._ghash_clmul"
                yield crypto_module_name + ".Hash._ghash_portable"
                yield crypto_module_name + ".Util._galois"

            elif full_name == crypto_module_name + ".Cipher.Salsa20":
                yield crypto_module_name + ".Cipher._Salsa20"

            elif full_name == crypto_module_name + ".Cipher.ChaCha20":
                yield crypto_module_name + ".Cipher._chacha20"

            elif full_name == crypto_module_name + ".PublicKey.ECC":
                yield crypto_module_name + ".PublicKey._ec_ws"
                yield crypto_module_name + ".PublicKey._ed25519"
                yield crypto_module_name + ".PublicKey._ed448"

            elif full_name == crypto_module_name + ".Cipher.ARC4":
                yield crypto_module_name + ".Cipher._ARC4"

            elif full_name == crypto_module_name + ".Cipher.PKCS1_v1_5":
                yield crypto_module_name + ".Cipher._pkcs1_decode"

            elif full_name == crypto_module_name + ".Math._IntegerCustom":
                yield crypto_module_name + ".Math._modexp"

        elif full_name in ("pynput.keyboard", "pynput.mouse"):
            if isMacOS():
                yield full_name.getChildNamed("_darwin")
            elif isWin32Windows():
                yield full_name.getChildNamed("_win32")
            else:
                yield full_name.getChildNamed("_xorg")
        elif full_name == "cryptography":
            yield "_cffi_backend"
        elif full_name == "bcrypt._bcrypt":
            yield "_cffi_backend"

    def getImplicitImports(self, module):
        full_name = module.getFullName()

        # TODO: This code absolutely doesn't belong here.
        # Read the .pyi file, and provide as implicit dependency.
        if module.isPythonExtensionModule():
            for used_module_name in module.getPyIModuleImportedNames():
                yield used_module_name

        if full_name == "pkg_resources.extern":
            # TODO: A package specific lookup of compile time "pkg_resources.extern" could
            # be done here, but this might be simpler to hardcode for now. Once we have
            # the infrastructure to ask a module that after optimization, we should do
            # that instead, as it will not use a separate process.
            for part in (
                "packaging",
                "pyparsing",
                "appdirs",
                "jaraco",
                "importlib_resources",
                "more_itertools",
                "six",
                "platformdirs",
            ):
                yield "pkg_resources._vendor." + part

        for item in self._getImportsByFullname(module=module, full_name=full_name):
            yield item

    def _getPackageExtraScanPaths(self, package_dir, config):
        for config_package_dir in config.get("package-dirs", ()):
            yield os.path.normpath(os.path.join(package_dir, "..", config_package_dir))

            yield package_dir

        for config_package_name in config.get("package-paths", ()):
            module_filename = self.locateModule(config_package_name)

            if module_filename is not None:
                if os.path.isfile(module_filename):
                    yield os.path.dirname(module_filename)
                else:
                    yield module_filename

    def getPackageExtraScanPaths(self, package_name, package_dir):
        for entry in self.config.get(package_name, section="import-hacks"):
            if self.evaluateCondition(
                full_name=package_name, condition=entry.get("when", "True")
            ):
                for item in self._getPackageExtraScanPaths(
                    package_dir=package_dir, config=entry
                ):
                    yield item

    def _getModuleSysPathAdditions(self, module_name, config):
        module_filename = self.locateModule(module_name)

        if os.path.isfile(module_filename):
            module_filename = yield os.path.dirname(module_filename)

        for relative_path in config.get("global-sys-path", ()):
            candidate = os.path.abspath(os.path.join(module_filename, relative_path))

            if os.path.isdir(candidate):
                yield candidate

    def getModuleSysPathAdditions(self, module_name):
        for entry in self.config.get(module_name, section="import-hacks"):
            if self.evaluateCondition(
                full_name=module_name, condition=entry.get("when", "True")
            ):
                for item in self._getModuleSysPathAdditions(
                    module_name=module_name, config=entry
                ):
                    yield item

    def onModuleSourceCode(self, module_name, source_code):
        if module_name == "numexpr.cpuinfo":

            # We cannot intercept "is" tests, but need it to be "isinstance",
            # so we patch it on the file. TODO: This is only temporary, in
            # the future, we may use optimization that understands the right
            # hand size of the "is" argument well enough to allow for our
            # type too.
            return source_code.replace(
                "type(attr) is types.MethodType", "isinstance(attr, types.MethodType)"
            )

        # Do nothing by default.
        return source_code

    def createPreModuleLoadCode(self, module):
        full_name = module.getFullName()

        for entry in self.config.get(full_name, section="implicit-imports"):
            if "pre-import-code" in entry:
                if self.evaluateCondition(
                    full_name=full_name, condition=entry.get("when", "True")
                ):
                    code = "\n".join(entry.get("pre-import-code"))

                    # TODO: Add a description to the Yaml file.
                    yield code, "According to Yaml configuration."

    def createPostModuleLoadCode(self, module):
        full_name = module.getFullName()

        for entry in self.config.get(full_name, section="implicit-imports"):
            if "post-import-code" in entry:
                if self.evaluateCondition(
                    full_name=full_name, condition=entry.get("when", "True")
                ):
                    code = "\n".join(entry.get("post-import-code"))

                    # TODO: Add a description to the Yaml file.
                    yield code, "According to Yaml configuration."

    unworthy_namespaces = (
        "setuptools",  # Not performance relevant.
        "distutils",  # Not performance relevant.
        "wheel",  # Not performance relevant.
        "pkg_resources",  # Not performance relevant.
        "pycparser",  # Not performance relevant.
        #        "cffi",  # Not performance relevant.
        "numpy.distutils",  # Largely unused, and a lot of modules.
        "numpy.f2py",  # Mostly unused, only numpy.distutils import it.
        "numpy.testing",  # Useless.
        "nose",  # Not performance relevant.
        "coverage",  # Not performance relevant.
        "docutils",  # Not performance relevant.
        "pytest",  # Not performance relevant.
        "_pytest",  # Not performance relevant.
        "unittest",  # Not performance relevant.
        "pexpect",  # Not performance relevant.
        "Cython",  # Mostly unused, and a lot of modules.
        "cython",
        "pyximport",
        "IPython",  # Mostly unused, and a lot of modules.
        "wx._core",  # Too large generated code
        "pyVmomi.ServerObjects",  # Too large generated code
        "pyglet.gl",  # Too large generated code
        "telethon.tl.types",  # Not performance relevant and slow C compile
        "importlib_metadata",  # Not performance relevant and slow C compile
        "comtypes.gen",  # Not performance relevant and slow C compile
        "win32com.gen_py",  # Not performance relevant and slow C compile
        "phonenumbers.geodata",  # Not performance relevant and slow C compile
        "site",  # Not performance relevant and problems with .pth files
        "packaging",  # Not performance relevant.
        "appdirs",  # Not performance relevant.
        "dropbox.team_log",  # Too large generated code
        "asyncua.ua.object_ids",  # Too large generated code
        "asyncua.ua.uaerrors._auto",  # Too large generated code
        "asyncua.server.standard_address_space.standard_address_space_services",  # Too large generated code
        "azure.mgmt.network",  # Too large generated code
        "azure.mgmt.compute",  # Too large generated code
        "transformers.utils.dummy_pt_objects",  # Not performance relevant.
        "transformers.utils.dummy_flax_objects",  # Not performance relevant.
        "transformers.utils.dummy_tf_objects",  # Not performance relevant.
    )

    def decideCompilation(self, module_name):
        if module_name.hasOneOfNamespaces(self.unworthy_namespaces):
            return "bytecode"
