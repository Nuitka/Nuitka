#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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

import os
import shutil

from nuitka.containers.oset import OrderedSet
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.PythonVersions import python_version
from nuitka.utils.FileOperations import getFileContentByLine
from nuitka.utils.SharedLibraries import locateDLL
from nuitka.utils.Utils import getOS


class NuitkaPluginPopularImplicitImports(NuitkaPluginBase):
    plugin_name = "implicit-imports"

    def __init__(self):
        NuitkaPluginBase.__init__(self)

        self.pkg_utils_externals = None
        self.opengl_plugins = None

    @staticmethod
    def isAlwaysEnabled():
        return True

    @staticmethod
    def _getImportsByFullname(full_name):
        """ Provides names of modules to imported implicitly.

        Notes:
            This methods works much like 'getImplicitImports', except that it
            accepts the search argument as a string. This allows callers to
            obtain results, which cannot provide a Nuitka module object.
        """
        # Many variables, branches, due to the many cases, pylint: disable=line-too-long,too-many-branches,too-many-statements

        elements = full_name.split(".")
        if elements[0] in ("PyQt4", "PyQt5"):
            if python_version < 300:
                yield "atexit", True

            # These are alternatives now:
            # TODO: One day it should avoid including both.
            yield "sip", False
            if elements[0] == "PyQt5":
                yield "PyQt5.sip", False

            child = elements[1] if len(elements) > 1 else None

            if child in (
                "QtGui",
                "QtAssistant",
                "QtDBus",
                "QtDeclarative",
                "QtSql",
                "QtDesigner",
                "QtHelp",
                "QtNetwork",
                "QtScript",
                "QtQml",
                "QtScriptTools",
                "QtSvg",
                "QtTest",
                "QtWebKit",
                "QtOpenGL",
                "QtXml",
                "QtXmlPatterns",
                "QtPrintSupport",
                "QtNfc",
                "QtWebKitWidgets",
                "QtBluetooth",
                "QtMultimediaWidgets",
                "QtQuick",
                "QtWebChannel",
                "QtWebSockets",
                "QtX11Extras",
                "_QOpenGLFunctions_2_0",
                "_QOpenGLFunctions_2_1",
                "_QOpenGLFunctions_4_1_Core",
            ):
                yield elements[0] + ".QtCore", True

            if child in (
                "QtDeclarative",
                "QtWebKit",
                "QtXmlPatterns",
                "QtQml",
                "QtPrintSupport",
                "QtWebKitWidgets",
                "QtMultimedia",
                "QtMultimediaWidgets",
                "QtQuick",
                "QtQuickWidgets",
                "QtWebSockets",
            ):
                yield elements[0] + ".QtNetwork", True

            if child == "QtScriptTools":
                yield elements[0] + ".QtScript", True

            if child in (
                "QtWidgets",
                "QtDeclarative",
                "QtDesigner",
                "QtHelp",
                "QtScriptTools",
                "QtSvg",
                "QtTest",
                "QtWebKit",
                "QtPrintSupport",
                "QtWebKitWidgets",
                "QtMultimedia",
                "QtMultimediaWidgets",
                "QtOpenGL",
                "QtQuick",
                "QtQuickWidgets",
                "QtSql",
                "_QOpenGLFunctions_2_0",
                "_QOpenGLFunctions_2_1",
                "_QOpenGLFunctions_4_1_Core",
            ):
                yield elements[0] + ".QtGui", True

            if full_name in (
                "PyQt5.QtDesigner",
                "PyQt5.QtHelp",
                "PyQt5.QtTest",
                "PyQt5.QtPrintSupport",
                "PyQt5.QtSvg",
                "PyQt5.QtOpenGL",
                "PyQt5.QtWebKitWidgets",
                "PyQt5.QtMultimediaWidgets",
                "PyQt5.QtQuickWidgets",
                "PyQt5.QtSql",
            ):
                yield "PyQt5.QtWidgets", True

            if full_name in ("PyQt5.QtPrintSupport",):
                yield "PyQt5.QtSvg", True

            if full_name in ("PyQt5.QtWebKitWidgets",):
                yield "PyQt5.QtWebKit", True
                yield "PyQt5.QtPrintSupport", True

            if full_name in ("PyQt5.QtMultimediaWidgets",):
                yield "PyQt5.QtMultimedia", True

            if full_name in ("PyQt5.QtQuick", "PyQt5.QtQuickWidgets"):
                yield "PyQt5.QtQml", True

            if full_name in ("PyQt5.QtQuickWidgets", "PyQt5.QtQml"):
                yield "PyQt5.QtQuick", True

            if full_name == "PyQt5.Qt":
                yield "PyQt5.QtCore", True
                yield "PyQt5.QtDBus", True
                yield "PyQt5.QtGui", True
                yield "PyQt5.QtNetwork", True
                yield "PyQt5.QtNetworkAuth", False
                yield "PyQt5.QtSensors", False
                yield "PyQt5.QtSerialPort", False
                yield "PyQt5.QtMultimedia", True
                yield "PyQt5.QtQml", False
                yield "PyQt5.QtWidgets", True

        elif full_name == "sip" and python_version < 300:
            yield "enum", False

        elif full_name == "PySide.QtDeclarative":
            yield "PySide.QtGui", True
        elif full_name == "PySide.QtHelp":
            yield "PySide.QtGui", True
        elif full_name == "PySide.QtOpenGL":
            yield "PySide.QtGui", True
        elif full_name == "PySide.QtScriptTools":
            yield "PySide.QtScript", True
            yield "PySide.QtGui", True
        elif full_name == "PySide.QtSql":
            yield "PySide.QtGui", True
        elif full_name == "PySide.QtSvg":
            yield "PySide.QtGui", True
        elif full_name == "PySide.QtTest":
            yield "PySide.QtGui", True
        elif full_name == "PySide.QtUiTools":
            yield "PySide.QtGui", True
            yield "PySide.QtXml", True
        elif full_name == "PySide.QtWebKit":
            yield "PySide.QtGui", True
        elif full_name == "PySide.phonon":
            yield "PySide.QtGui", True
        elif full_name == "lxml.etree":
            yield "gzip", True
            yield "lxml._elementpath", True
        elif full_name == "gtk._gtk":
            yield "pangocairo", True
            yield "pango", True
            yield "cairo", True
            yield "gio", True
            yield "atk", True
        elif full_name == "atk":
            yield "gobject", True
        elif full_name == "gtkunixprint":
            yield "gobject", True
            yield "cairo", True
            yield "gtk", True
        elif full_name == "pango":
            yield "gobject", True
        elif full_name == "pangocairo":
            yield "pango", True
            yield "cairo", True
        elif full_name == "reportlab.rl_config":
            yield "reportlab.rl_settings", True
        elif full_name == "socket":
            yield "_socket", False
        elif full_name == "ctypes":
            yield "_ctypes", True
        elif full_name == "gi._gi":
            yield "gi._error", True
        elif full_name == "gi._gi_cairo":
            yield "cairo", True
        elif full_name == "cairo._cairo":
            yield "gi._gobject", False
        elif full_name in ("Tkinter", "tkinter"):
            yield "_tkinter", False
        elif full_name in (
            "cryptography.hazmat.bindings._openssl",
            "cryptography.hazmat.bindings._constant_time",
            "cryptography.hazmat.bindings._padding",
        ):
            yield "_cffi_backend", True
        elif full_name.startswith("cryptography._Cryptography_cffi_"):
            yield "_cffi_backend", True
        elif full_name == "bcrypt._bcrypt":
            yield "_cffi_backend", True
        elif full_name == "nacl._sodium":
            yield "_cffi_backend", True
        elif full_name == "_dbus_glib_bindings":
            yield "_dbus_bindings", True
        elif full_name == "_mysql":
            yield "_mysql_exceptions", True
        elif full_name == "lxml.objectify":
            yield "lxml.etree", True
        elif full_name == "_yaml":
            yield "yaml", True
        elif full_name == "apt_inst":
            yield "apt_pkg", True

        # start of gevent imports --------------------------------------------
        elif full_name == "gevent":
            yield "_cffi_backend", True
            yield "gevent._config", True
            yield "gevent.core", True
            yield "gevent.resolver_thread", True
            yield "gevent.resolver_ares", True
            yield "gevent.socket", True
            yield "gevent.threadpool", True
            yield "gevent.thread", True
            yield "gevent.threading", True
            yield "gevent.select", True
            yield "gevent.hub", True
            yield "gevent.greenlet", True
            yield "gevent.local", True
            yield "gevent.event", True
            yield "gevent.queue", True
            yield "gevent.resolver", True
            yield "gevent.subprocess", True
            if getOS() == "Windows":
                yield "gevent.libuv", True
            else:
                yield "gevent.libev", True

        elif full_name == "gevent.hub":
            yield "gevent._hub_primitives", True
            yield "gevent._greenlet_primitives", True
            yield "gevent._hub_local", True
            yield "gevent._waiter", True
            yield "gevent._util", True
            yield "gevent._ident", True
            yield "gevent.exceptions", True

        elif full_name == "gevent.libev":
            yield "gevent.libev.corecext", True
            yield "gevent.libev.corecffi", True
            yield "gevent.libev.watcher", True

        elif full_name == "gevent.libuv":
            yield "gevent._interfaces", True
            yield "gevent._ffi", True
            yield "gevent.libuv.loop", True
            yield "gevent.libuv.watcher", True

        elif full_name == "gevent.libuv.loop":
            yield "gevent.libuv._corecffi", True
            yield "gevent._interfaces", True

        elif full_name == "gevent._ffi":
            yield "gevent._ffi.loop", True
            yield "gevent._ffi.callback", True
            yield "gevent._ffi.watcher", True

        elif full_name == "gevent._waiter":
            yield "gevent.__waiter", True

        elif full_name == "gevent._hub_local":
            yield "gevent.__hub_local", True
            yield "gevent.__greenlet_primitives", True

        elif full_name == "gevent._hub_primitives":
            yield "gevent.__hub_primitives", True

        elif full_name == "gevent.greenlet":
            yield "gevent._hub_local", True
            yield "gevent._greenlet", True

        elif full_name == "gevent._greenlet":
            yield "gevent.__ident", True

        elif full_name == "gevent.monkey":
            yield "gevent.builtins", True
            yield "gevent.time", True
            yield "gevent.local", True
            yield "gevent.ssl", True
            yield "gevent.events", True

        elif full_name == "gevent.resolver":
            yield "gevent.resolver.blocking", True
            yield "gevent.resolver.cares", True
            yield "gevent.resolver.thread", True

        elif full_name == "gevent._semaphore":
            yield "gevent._abstract_linkable", True
            yield "gevent.__semaphore", True

        elif full_name == "gevent._abstract_linkable":
            yield "gevent.__abstract_linkable", True

        elif full_name == "gevent.local":
            yield "gevent._local", True

        elif full_name == "gevent.event":
            yield "gevent._event", True

        elif full_name == "gevent.queue":
            yield "gevent._queue", True

        elif full_name == "gevent.pool":
            yield "gevent._imap", True

        elif full_name == "gevent._imap":
            yield "gevent.__imap", True
        # end of gevent imports ----------------------------------------------

        # start of tensorflow imports --------------------------------------------

        elif full_name == "tensorflow":
            yield "tensorboard", False
            yield "tensorflow_estimator", False

        elif full_name == "tensorflow.python":
            yield "tensorflow.python._pywrap_tensorflow_internal", True
            yield "tensorflow.python.ops", False
            yield "tensorflow.python.ops.cond_v2", False

        elif full_name == "tensorflow.lite.python.interpreter_wrapper":
            yield "tensorflow.lite.python.interpreter_wrapper._tensorflow_wrap_interpreter_wrapper", False

        elif full_name == "tensorflow.lite.python.optimize":
            yield "tensorflow.lite.python.optimize._tensorflow_lite_wrap_calibration_wrapper", False

        elif full_name == "tensorflow.lite.toco.python":
            yield "tensorflow.lite.toco.python._tensorflow_wrap_toco", False

        # the remaining entries are relevant non-Windows platforms only
        elif elements[0] == "tensorflow" and getOS() != "Windows":
            if (
                full_name
                == "tensorflow.include.external.protobuf_archive.python.google.protobuf.internal"
            ):
                yield "tensorflow.include.external.protobuf_archive.python.google.protobuf.internal._api_implementation", False

            elif (
                full_name
                == "tensorflow.include.external.protobuf_archive.python.google.protobuf.pyext"
            ):
                yield "tensorflow.include.external.protobuf_archive.python.google.protobuf.pyext._message", False

            elif full_name == "tensorflow.python.framework":
                yield "tensorflow.python.framework.fast_tensor_util", False

            elif full_name == "tensorflow.compiler.tf2tensorrt":
                yield "tensorflow.compiler.tf2tensorrt._wrap_py_utils", False

            elif full_name == "tensorflow.compiler.tf2tensorrt.python.ops":
                yield "tensorflow.compiler.tf2tensorrt.python.ops.libtftrt", False

            elif full_name == "tensorflow.compiler.tf2xla.ops":
                yield "tensorflow.compiler.tf2xla.ops._xla_ops", False

            elif full_name == "tensorflow.contrib.tensor_forest":
                yield "tensorflow.contrib.tensor_forest.libforestprotos", False

            elif full_name == "tensorflow.contrib.tensor_forest.python.ops":
                yield "tensorflow.contrib.tensor_forest.python.ops._model_ops", False
                yield "tensorflow.contrib.tensor_forest.python.ops._stats_ops", False
                yield "tensorflow.contrib.tensor_forest.python.ops._tensor_forest_ops", False

            elif full_name == "tensorflow.contrib.tensor_forest.hybrid.python.ops":
                yield "tensorflow.contrib.tensor_forest.hybrid.python.ops._training.ops", False

            elif full_name == "tensorflow.contrib.resampler.python.ops":
                yield "tensorflow.contrib.resampler.python.ops._resampler_ops", False

            elif full_name == "tensorflow.contrib.nearest_neighbor.python.ops":
                yield "tensorflow.contrib.nearest_neighbor.python.ops._nearest_neighbor_ops", False

            elif full_name == "tensorflow.contrib.ignite":
                yield "tensorflow.contrib.ignite._ignite_ops", False

            elif full_name == "tensorflow.contrib.kinesis":
                yield "tensorflow.contrib.kinesis._dataset_ops", False

            elif full_name == "tensorflow.contrib.ffmpeg":
                yield "tensorflow.contrib.ffmpeg.ffmpeg", False

            elif full_name == "tensorflow.contrib.framework.python.ops":
                yield "tensorflow.contrib.framework.python.ops._variable_ops", False

            elif full_name == "tensorflow.contrib.text.python.ops":
                yield "tensorflow.contrib.text.python.ops._skip_gram_ops", False

            elif full_name == "tensorflow.contrib.reduce_slice_ops.python.ops":
                yield "tensorflow.contrib.reduce_slice_ops.python.ops._reduce_slice_ops", False

            elif full_name == "tensorflow.contrib.periodic_resample.python.ops":
                yield "tensorflow.contrib.periodic_resample.python.ops._periodic_resample_op", False

            elif full_name == "tensorflow.contrib.memory_stats.python.ops":
                yield "tensorflow.contrib.memory_stats.python.ops._memory_stats_ops", False

            elif full_name == "tensorflow.contrib.libsvm.python.ops":
                yield "tensorflow.contrib.libsvm.python.ops._libsvm_ops", False

            elif full_name == "tensorflow.contrib.fused_conv.python.ops":
                yield "tensorflow.contrib.fused_conv.python.ops._fused_conv2d_bias_activation_op", False

            elif full_name == "tensorflow.contrib.kafka":
                yield "tensorflow.contrib.kafka._dataset_ops", False

            elif full_name == "tensorflow.contrib.hadoop":
                yield "tensorflow.contrib.hadoop._dataset_ops", False

            elif full_name == "tensorflow.contrib.seq2seq.python.ops":
                yield "tensorflow.contrib.seq2seq.python.ops._beam_search_ops", False

            elif full_name == "tensorflow.contrib.rpc.python.kernel_tests":
                yield "tensorflow.contrib.rpc.python.kernel_tests.libtestexample", False

            elif full_name == "tensorflow.contrib.boosted_trees.python.ops":
                yield "tensorflow.contrib.boosted_trees.python.ops._boosted_trees_ops", False

            elif full_name == "tensorflow.contrib.layers.python.ops":
                yield "tensorflow.contrib.layers.python.ops._sparse_feature_cross_op", False

            elif full_name == "tensorflow.contrib.image.python.ops":
                yield "tensorflow.contrib.image.python.ops._distort_image_ops", False
                yield "tensorflow.contrib.image.python.ops._image_ops", False
                yield "tensorflow.contrib.image.python.ops._single_image_random_dot_stereograms", False

            elif full_name == "tensorflow.contrib.factorization.python.ops":
                yield "tensorflow.contrib.factorization.python.ops._factorization_ops", False

            elif full_name == "tensorflow.contrib.input_pipeline.python.ops":
                yield "tensorflow.contrib.input_pipeline.python.ops._input_pipeline_ops", False

            elif full_name == "tensorflow.contrib.rnn.python.ops":
                yield "tensorflow.contrib.rnn.python.ops._gru_ops", False
                yield "tensorflow.contrib.rnn.python.ops._lstm_ops", False

            elif full_name == "tensorflow.contrib.bigtable.python.ops":
                yield "tensorflow.contrib.bigtable.python.ops._bigtable", False

        # end of tensorflow imports -------------------------------------------

        # OpenCV imports ------------------------------------------------------
        elif full_name == "cv2":
            yield "numpy", True
            yield "numpy.core", True

        # chainer imports -----------------------------------------------------
        elif full_name == "chainer":
            yield "chainer.distributions", True
            yield "chainer.distributions.utils", True

        # numpy imports -------------------------------------------------------
        elif full_name == "numpy":
            yield "numpy._mklinit", False
        elif full_name == "numpy.core":
            yield "numpy.core._dtype_ctypes", False

        # matplotlib imports --------------------------------------------------
        elif full_name == "matplotlib":
            yield "matplotlib.backend_managers", True
            yield "matplotlib.backend_bases", True

        elif full_name == "matplotlib.backends.backend_agg":
            yield "matplotlib.backends._backend_agg", True
            yield "matplotlib.backends._tkagg", True
            yield "matplotlib.backends.backend_tkagg", True

        # scipy imports -------------------------------------------------------
        elif full_name == "scipy.special":
            yield "scipy.special._ufuncs_cxx", True
        elif full_name == "scipy.linalg":
            yield "scipy.linalg.cython_blas", True
            yield "scipy.linalg.cython_lapack", True
        elif full_name == "scipy.sparse.csgraph":
            yield "scipy.sparse.csgraph._validation", True
        elif full_name == "scipy._lib":
            yield "scipy._lib.messagestream", True

        # scikit-learn imports ------------------------------------------------
        elif full_name == "sklearn.utils.sparsetools":
            yield "sklearn.utils.sparsetools._graph_validation", True
            yield "sklearn.utils.sparsetools._graph_tools", True

        elif full_name == "sklearn.utils":
            yield "sklearn.utils.lgamma", True
            yield "sklearn.utils.weight_vector", True
            yield "sklearn.utils._unittest_backport", False

        elif full_name == "PIL._imagingtk":
            yield "PIL._tkinter_finder", True

        elif full_name == "pkg_resources._vendor.packaging":
            yield "pkg_resources._vendor.packaging.version", True
            yield "pkg_resources._vendor.packaging.specifiers", True
            yield "pkg_resources._vendor.packaging.requirements", True

        elif full_name == "uvloop.loop":
            yield "uvloop._noop", True
        elif full_name == "fitz.fitz":
            yield "fitz._fitz", True
        elif full_name == "pandas._libs":
            yield "pandas._libs.tslibs.np_datetime", False
            yield "pandas._libs.tslibs.nattype", False
        elif full_name == "pandas.core.window":
            yield "pandas._libs.skiplist", False
        elif full_name == "zmq.backend":
            yield "zmq.backend.cython", True

        # Support for both pycryotodome (module name Crypto) and pycyptodomex (module name Cryptodome)
        elif full_name.split(".")[0] in ("Crypto", "Cryptodome"):
            crypto_module_name = full_name.split(".")[0]
            if full_name == crypto_module_name + ".Util._raw_api":
                for module_name in (
                    "_raw_aes",
                    "_raw_aesni",
                    "_raw_arc2",
                    "_raw_blowfish",
                    "_raw_cast",
                    "_raw_cbc",
                    "_raw_cfb",
                    "_raw_ctr",
                    "_raw_des",
                    "_raw_des3",
                    "_raw_ecb",
                    "_raw_ocb",
                    "_raw_ofb",
                ):
                    if full_name == crypto_module_name + ".Util._raw_api":
                        yield crypto_module_name + ".Cipher." + module_name, True
            elif full_name == crypto_module_name + ".Util.strxor":
                yield crypto_module_name + ".Util._strxor", True
            elif full_name == crypto_module_name + ".Util._cpu_features":
                yield crypto_module_name + ".Util._cpuid_c", True
            elif full_name == crypto_module_name + ".Hash.BLAKE2s":
                yield crypto_module_name + ".Hash._BLAKE2s", True
            elif full_name == crypto_module_name + ".Hash.SHA1":
                yield crypto_module_name + ".Hash._SHA1", True
            elif full_name == crypto_module_name + ".Hash.SHA224":
                yield crypto_module_name + ".Hash._SHA224", True
            elif full_name == crypto_module_name + ".Hash.SHA256":
                yield crypto_module_name + ".Hash._SHA256", True
            elif full_name == crypto_module_name + ".Hash.SHA384":
                yield crypto_module_name + ".Hash._SHA384", True
            elif full_name == crypto_module_name + ".Hash.SHA512":
                yield crypto_module_name + ".Hash._SHA512", True
            elif full_name == crypto_module_name + ".Hash.MD5":
                yield crypto_module_name + ".Hash._MD5", True
            elif full_name == crypto_module_name + ".Protocol.KDF":
                yield crypto_module_name + ".Cipher._Salsa20", True
                yield crypto_module_name + ".Protocol._scrypt", True
            elif full_name == crypto_module_name + ".Cipher._mode_gcm":
                yield crypto_module_name + ".Hash._ghash_portable", True
        elif full_name == "pycparser.c_parser":
            yield "pycparser.yacctab", True
            yield "pycparser.lextab", True
        elif full_name == "passlib.hash":
            yield "passlib.handlers.sha2_crypt", True

    def getImportsByFullname(self, full_name):
        """ Recursively create a set of imports for a fullname.

        Notes:
            If an imported item has imported kids, call me again with each kid,
            resulting in a leaf-only set (no more consequential kids).
        """
        result = OrderedSet()

        def checkImportsRecursive(module_name):
            for item in self._getImportsByFullname(module_name):
                if item not in result:
                    result.add(item)
                    checkImportsRecursive(item[0])

        checkImportsRecursive(full_name)

        return result

    def getImplicitImports(self, module):
        # Many variables, branches, due to the many cases, pylint: disable=too-many-branches
        full_name = module.getFullName()

        if module.isPythonShlibModule():
            for used_module in module.getUsedModules():
                yield used_module[0], False

        if full_name == "pkg_resources.extern":
            if self.pkg_utils_externals is None:
                for line in getFileContentByLine(module.getCompileTimeFilename()):
                    if line.startswith("names"):
                        line = line.split("=")[-1].strip()
                        parts = line.split(",")

                        self.pkg_utils_externals = [part.strip("' ") for part in parts]

                        break
                else:
                    self.pkg_utils_externals = ()

            for pkg_util_external in self.pkg_utils_externals:
                yield "pkg_resources._vendor." + pkg_util_external, False

        elif full_name == "OpenGL":
            if self.opengl_plugins is None:
                self.opengl_plugins = []

                for line in getFileContentByLine(module.getCompileTimeFilename()):
                    if line.startswith("PlatformPlugin("):
                        os_part, plugin_name_part = line[15:-1].split(",")
                        os_part = os_part.strip("' ")
                        plugin_name_part = plugin_name_part.strip(") '")
                        plugin_name_part = plugin_name_part[
                            : plugin_name_part.rfind(".")
                        ]
                        if os_part == "nt":
                            if getOS() == "Windows":
                                self.opengl_plugins.append(plugin_name_part)
                        elif os_part.startswith("linux"):
                            if getOS() == "Linux":
                                self.opengl_plugins.append(plugin_name_part)
                        elif os_part.startswith("darwin"):
                            if getOS() == "Darwin":
                                self.opengl_plugins.append(plugin_name_part)
                        elif os_part.startswith(("posix", "osmesa", "egl")):
                            if getOS() != "Windows":
                                self.opengl_plugins.append(plugin_name_part)
                        else:
                            assert False, os_part

            for opengl_plugin in self.opengl_plugins:
                yield opengl_plugin, True

        else:
            # create a flattened import set for full_name and yield from it
            for item in self.getImportsByFullname(full_name):
                yield item

    # We don't care about line length here, pylint: disable=line-too-long

    module_aliases = {
        "six.moves.builtins": "__builtin__" if python_version < 300 else "builtins",
        "six.moves.configparser": "ConfigParser"
        if python_version < 300
        else "configparser",
        "six.moves.copyreg": "copy_reg" if python_version < 300 else "copyreg",
        "six.moves.dbm_gnu": "gdbm" if python_version < 300 else "dbm.gnu",
        "six.moves._dummy_thread": "dummy_thread"
        if python_version < 300
        else "_dummy_thread",
        "six.moves.http_cookiejar": "cookielib"
        if python_version < 300
        else "http.cookiejar",
        "six.moves.http_cookies": "Cookie" if python_version < 300 else "http.cookies",
        "six.moves.html_entities": "htmlentitydefs"
        if python_version < 300
        else "html.entities",
        "six.moves.html_parser": "HTMLParser"
        if python_version < 300
        else "html.parser",
        "six.moves.http_client": "httplib" if python_version < 300 else "http.client",
        "six.moves.email_mime_multipart": "email.MIMEMultipart"
        if python_version < 300
        else "email.mime.multipart",
        "six.moves.email_mime_nonmultipart": "email.MIMENonMultipart"
        if python_version < 300
        else "email.mime.nonmultipart",
        "six.moves.email_mime_text": "email.MIMEText"
        if python_version < 300
        else "email.mime.text",
        "six.moves.email_mime_base": "email.MIMEBase"
        if python_version < 300
        else "email.mime.base",
        "six.moves.BaseHTTPServer": "BaseHTTPServer"
        if python_version < 300
        else "http.server",
        "six.moves.CGIHTTPServer": "CGIHTTPServer"
        if python_version < 300
        else "http.server",
        "six.moves.SimpleHTTPServer": "SimpleHTTPServer"
        if python_version < 300
        else "http.server",
        "six.moves.cPickle": "cPickle" if python_version < 300 else "pickle",
        "six.moves.queue": "Queue" if python_version < 300 else "queue",
        "six.moves.reprlib": "repr" if python_version < 300 else "reprlib",
        "six.moves.socketserver": "SocketServer"
        if python_version < 300
        else "socketserver",
        "six.moves._thread": "thread" if python_version < 300 else "_thread",
        "six.moves.tkinter": "Tkinter" if python_version < 300 else "tkinter",
        "six.moves.tkinter_dialog": "Dialog"
        if python_version < 300
        else "tkinter.dialog",
        "six.moves.tkinter_filedialog": "FileDialog"
        if python_version < 300
        else "tkinter.filedialog",
        "six.moves.tkinter_scrolledtext": "ScrolledText"
        if python_version < 300
        else "tkinter.scrolledtext",
        "six.moves.tkinter_simpledialog": "SimpleDialog"
        if python_version < 300
        else "tkinter.simpledialog",
        "six.moves.tkinter_tix": "Tix" if python_version < 300 else "tkinter.tix",
        "six.moves.tkinter_ttk": "ttk" if python_version < 300 else "tkinter.ttk",
        "six.moves.tkinter_constants": "Tkconstants"
        if python_version < 300
        else "tkinter.constants",
        "six.moves.tkinter_dnd": "Tkdnd" if python_version < 300 else "tkinter.dnd",
        "six.moves.tkinter_colorchooser": "tkColorChooser"
        if python_version < 300
        else "tkinter_colorchooser",
        "six.moves.tkinter_commondialog": "tkCommonDialog"
        if python_version < 300
        else "tkinter_commondialog",
        "six.moves.tkinter_tkfiledialog": "tkFileDialog"
        if python_version < 300
        else "tkinter.filedialog",
        "six.moves.tkinter_font": "tkFont" if python_version < 300 else "tkinter.font",
        "six.moves.tkinter_messagebox": "tkMessageBox"
        if python_version < 300
        else "tkinter.messagebox",
        "six.moves.tkinter_tksimpledialog": "tkSimpleDialog"
        if python_version < 300
        else "tkinter_tksimpledialog",
        "six.moves.urllib_parse": None if python_version < 300 else "urllib.parse",
        "six.moves.urllib_error": None if python_version < 300 else "urllib.error",
        "six.moves.urllib_robotparser": "robotparser"
        if python_version < 300
        else "urllib.robotparser",
        "six.moves.xmlrpc_client": "xmlrpclib"
        if python_version < 300
        else "xmlrpc.client",
        "six.moves.xmlrpc_server": "SimpleXMLRPCServer"
        if python_version < 300
        else "xmlrpc.server",
        "six.moves.winreg": "_winreg" if python_version < 300 else "winreg",
        "requests.packages.urllib3": "urllib3",
        "requests.packages.urllib3.contrib": "urllib3.contrib",
        "requests.packages.urllib3.contrib.pyopenssl": "urllib3.contrib.pyopenssl",
        "requests.packages.urllib3.contrib.ntlmpool": "urllib3.contrib.ntlmpool",
        "requests.packages.urllib3.contrib.socks": "urllib3.contrib.socks",
        "requests.packages.urllib3.exceptions": "urllib3.exceptions",
        "requests.packages.urllib3._collections": "urllib3._collections",
        "requests.packages.chardet": "chardet",
        "requests.packages.idna": "idna",
        "requests.packages.urllib3.packages": "urllib3.packages",
        "requests.packages.urllib3.packages.ordered_dict": "urllib3.packages.ordered_dict",
        "requests.packages.urllib3.packages.ssl_match_hostname": "urllib3.packages.ssl_match_hostname",
        "requests.packages.urllib3.packages.ssl_match_hostname._implementation": "urllib3.packages.ssl_match_hostname._implementation",
        "requests.packages.urllib3.connectionpool": "urllib3.connectionpool",
        "requests.packages.urllib3.connection": "urllib3.connection",
        "requests.packages.urllib3.filepost": "urllib3.filepost",
        "requests.packages.urllib3.request": "urllib3.request",
        "requests.packages.urllib3.response": "urllib3.response",
        "requests.packages.urllib3.fields": "urllib3.fields",
        "requests.packages.urllib3.poolmanager": "urllib3.poolmanager",
        "requests.packages.urllib3.util": "urllib3.util",
        "requests.packages.urllib3.util.connection": "urllib3.util.connection",
        "requests.packages.urllib3.util.request": "urllib3.util.request",
        "requests.packages.urllib3.util.response": "urllib3.util.response",
        "requests.packages.urllib3.util.retry": "urllib3.util.retry",
        "requests.packages.urllib3.util.ssl_": "urllib3.util.ssl_",
        "requests.packages.urllib3.util.timeout": "urllib3.util.timeout",
        "requests.packages.urllib3.util.url": "urllib3.util.url",
    }

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

    def suppressBuiltinImportWarning(self, module, source_ref):
        if module.getFullName() in ("setuptools",):
            return True

        if module.getName() == "six":
            return True

        return False

    def considerExtraDlls(self, dist_dir, module):
        full_name = module.getFullName()

        if full_name == "uuid" and getOS() == "Linux":
            uuid_dll_path = locateDLL("uuid")
            dist_dll_path = os.path.join(dist_dir, os.path.basename(uuid_dll_path))

            shutil.copy(uuid_dll_path, dist_dll_path)

            return ((uuid_dll_path, dist_dll_path, None),)
        elif full_name == "iptc" and getOS() == "Linux":
            import iptc.util  # pylint: disable=I0021,import-error

            xtwrapper_dll = iptc.util.find_library("xtwrapper")[0]
            xtwrapper_dll_path = xtwrapper_dll._name  # pylint: disable=protected-access

            dist_dll_path = os.path.join(dist_dir, os.path.basename(xtwrapper_dll_path))

            shutil.copy(xtwrapper_dll_path, dist_dll_path)

            return ((xtwrapper_dll_path, dist_dll_path, None),)

        return ()

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
    )

    def decideCompilation(self, module_name, source_ref):
        for unworthy_namespace in self.unworthy_namespaces:
            if module_name == unworthy_namespace or module_name.startswith(
                unworthy_namespace + "."
            ):
                return "bytecode"
