#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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
import sys

from nuitka.containers.oset import OrderedSet
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.PythonVersions import python_version
from nuitka.utils.FileOperations import getFileContentByLine
from nuitka.utils.SharedLibraries import getPyWin32Dir, locateDLL
from nuitka.utils.Utils import getOS, isWin32Windows


def remove_suffix(mod_dir, mod_name):
    """Return the path of a module's first level name.

    """
    if mod_name not in mod_dir:
        return mod_dir
    p = mod_dir.find(mod_name) + len(mod_name)
    return mod_dir[:p]


def remove_prefix(mod_dir, mod_name):
    """Return the tail of a module's path.

    Remove everything preceding the top level name.
    """
    if mod_name not in mod_dir:
        return mod_dir
    p = mod_dir.find(mod_name)
    return mod_dir[p:]


_added_pywin32 = False


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
    def _getImportsByFullname(full_name, package_dir):
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
                yield elements[0] + ".QtCore", False

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
                "QtWebEngineWidgets",
            ):
                yield elements[0] + ".QtNetwork", False

            if child == "QtWebEngineWidgets":
                yield elements[0] + ".QtWebEngineCore", False
                yield elements[0] + ".QtWebChannel", False
                yield elements[0] + ".QtPrintSupport", False

            if child == "QtScriptTools":
                yield elements[0] + ".QtScript", False

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
                yield elements[0] + ".QtGui", False

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
                yield "PyQt5.QtWidgets", False

            if full_name in ("PyQt5.QtPrintSupport",):
                yield "PyQt5.QtSvg", False

            if full_name in ("PyQt5.QtWebKitWidgets",):
                yield "PyQt5.QtWebKit", False
                yield "PyQt5.QtPrintSupport", False

            if full_name in ("PyQt5.QtMultimediaWidgets",):
                yield "PyQt5.QtMultimedia", False

            if full_name in ("PyQt5.QtQuick", "PyQt5.QtQuickWidgets"):
                yield "PyQt5.QtQml", False

            if full_name in ("PyQt5.QtQuickWidgets", "PyQt5.QtQml"):
                yield "PyQt5.QtQuick", False

            if full_name == "PyQt5.Qt":
                yield "PyQt5.QtCore", False
                yield "PyQt5.QtDBus", False
                yield "PyQt5.QtGui", False
                yield "PyQt5.QtNetwork", False
                yield "PyQt5.QtNetworkAuth", False
                yield "PyQt5.QtSensors", False
                yield "PyQt5.QtSerialPort", False
                yield "PyQt5.QtMultimedia", False
                yield "PyQt5.QtQml", False
                yield "PyQt5.QtWidgets", False

        elif full_name == "sip" and python_version < 300:
            yield "enum", False

        elif full_name == "PySide.QtDeclarative":
            yield "PySide.QtGui", False
        elif full_name == "PySide.QtHelp":
            yield "PySide.QtGui", False
        elif full_name == "PySide.QtOpenGL":
            yield "PySide.QtGui", False
        elif full_name == "PySide.QtScriptTools":
            yield "PySide.QtScript", False
            yield "PySide.QtGui", False
        elif full_name == "PySide.QtSql":
            yield "PySide.QtGui", False
        elif full_name == "PySide.QtSvg":
            yield "PySide.QtGui", False
        elif full_name == "PySide.QtTest":
            yield "PySide.QtGui", False
        elif full_name == "PySide.QtUiTools":
            yield "PySide.QtGui", False
            yield "PySide.QtXml", False
        elif full_name == "PySide.QtWebKit":
            yield "PySide.QtGui", False
        elif full_name == "PySide.phonon":
            yield "PySide.QtGui", False

        elif full_name == "lxml":
            yield "lxml.builder", False
            yield "lxml.etree", False
            yield "lxml.objectify", False
            yield "lxml.sax", False
            yield "lxml._elementpath", False

        elif full_name == "lxml.etree":
            yield "lxml._elementpath", False

        elif full_name == "lxml.html":
            yield "lxml.html.clean", False
            yield "lxml.html.diff", False
            yield "lxml.etree", False

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

        # start of engineio imports ------------------------------------------
        elif full_name == "engineio":
            yield "engineio.async_drivers", False

        elif full_name == "engineio.async_drivers":
            yield "engineio.async_drivers.aiohttp", False
            yield "engineio.async_drivers.asgi", False
            yield "engineio.async_drivers.eventlet", False
            yield "engineio.async_drivers.gevent", False
            yield "engineio.async_drivers.gevent_uwsgi", False
            yield "engineio.async_drivers.sanic", False
            yield "engineio.async_drivers.threading", False
            yield "engineio.async_drivers.tornado", False

        # start of eventlet imports ------------------------------------------
        elif full_name == "eventlet":
            yield "eventlet.hubs", False

        elif full_name == "eventlet.hubs":
            yield "eventlet.hubs.epolls", False
            yield "eventlet.hubs.hub", False
            yield "eventlet.hubs.kqueue", False
            yield "eventlet.hubs.poll", False
            yield "eventlet.hubs.pyevent", False
            yield "eventlet.hubs.selects", False
            yield "eventlet.hubs.timer", False

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

        # start of tensorflow imports ----------------------------------------
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

        # boto3 imports ------------------------------------------------------
        elif full_name == "boto3":
            yield "boto3.ec2", False
            yield "boto3.ec2.createtags", False
            yield "boto3.ec2.deletetags", False
            yield "boto3.dynamodb", False
            yield "boto3.s3", False
            yield "boto3.s3.inject", False
            yield "boto3.s3.transfer", False

        # GDAL imports ------------------------------------------------------
        elif full_name == "osgeo":
            yield "osgeo._gdal", False
            yield "osgeo._gdalconst", False
            yield "osgeo._gdal_array", False
            yield "osgeo._gnm", False
            yield "osgeo._ogr", False
            yield "osgeo._osr", False

        # OpenCV imports ------------------------------------------------------
        elif full_name == "cv2":
            yield "numpy", True
            yield "numpy.core", True

        # fastapi imports ---------------------------------------------------
        elif full_name == "fastapi":
            yield "fastapi.routing", True

        # pydantic imports ---------------------------------------------------
        elif full_name == "pydantic":
            yield "pydantic.typing", False
            yield "pydantic.fields", False
            yield "pydantic.utils", False
            yield "pydantic.schema", False
            yield "pydantic.env_settings", False
            yield "pydantic.main", False
            yield "pydantic.error_wrappers", False
            yield "pydantic.validators", False
            yield "pydantic.mypy", False
            yield "pydantic.version", False
            yield "pydantic.types", False
            yield "pydantic.color", False
            yield "pydantic.parse", False
            yield "pydantic.json", False
            yield "pydantic.datetime_parse", False
            yield "pydantic.dataclasses", False
            yield "pydantic.class_validators", False
            yield "pydantic.networks", False
            yield "pydantic.errors", False

        # uvicorn imports -----------------------------------------------------
        elif full_name == "uvicorn":
            yield "uvicorn.loops", False
            yield "uvicorn.lifespan", False
            yield "uvicorn.protocols", False
        elif full_name == "uvicorn.config":
            yield "uvicorn.logging", False
        elif full_name == "uvicorn.lifespan":
            yield "uvicorn.lifespan.off", False
            yield "uvicorn.lifespan.on", False
        elif full_name == "uvicorn.loops":
            yield "uvicorn.loops.auto", False
            yield "uvicorn.loops.uvloop", False
        elif full_name == "uvicorn.protocols":
            yield "uvicorn.protocols.http", False
            yield "uvicorn.protocols.websockets", False
        elif full_name == "uvicorn.protocols.http":
            yield "uvicorn.protocols.http.auto", False
            yield "uvicorn.protocols.http.h11_impl", False
            yield "uvicorn.protocols.http.httptools_impl", False
        elif full_name == "uvicorn.protocols.websockets":
            yield "uvicorn.protocols.websockets.auto", False
            yield "uvicorn.protocols.websockets.websockets_impl", False
            yield "uvicorn.protocols.websockets.wsproto_impl", False

        # vtk imports -----------------------------------------------------
        elif full_name == "vtkmodules":
            yield "vtkmodules.all", False
            yield "vtkmodules.util", False

        elif full_name == "vtkmodules.util":
            yield "vtkmodules.util.misc", False
            yield "vtkmodules.util.numpy_support", False
            yield "vtkmodules.util.vtkAlgorithm", False
            yield "vtkmodules.util.vtkConstants", False
            yield "vtkmodules.util.vtkImageExportToArray", False
            yield "vtkmodules.util.vtkImageImportFromArray", False
            yield "vtkmodules.util.vtkMethodParser", False
            yield "vtkmodules.util.vtkVariant", False

        elif full_name == "vtkmodules.qt":
            yield "vtkmodules.qt.QVTKRenderWindowInteractor", False

        elif full_name == "vtkmodules.tk":
            yield "vtkmodules.tk.vtkLoadPythonTkWidgets", False
            yield "vtkmodules.tk.vtkTkImageViewerWidget", False
            yield "vtkmodules.tk.vtkTkPhotoImage", False
            yield "vtkmodules.tk.vtkTkRenderWidget", False
            yield "vtkmodules.tk.vtkTkRenderWindowInteractor", False

        elif full_name == "vtkmodules.wx":
            yield "vtkmodules.wx.wxVTKRenderWindow", False
            yield "vtkmodules.wx.wxVTKRenderWindowInteractor", False

        # chainer imports -----------------------------------------------------
        elif full_name == "chainer":
            yield "chainer.distributions", False
            yield "chainer.distributions.utils", False

        elif full_name == "chainer.distributions":
            yield "chainer.distributions.utils", False

        # numpy imports -------------------------------------------------------
        elif full_name == "numpy":
            yield "numpy._mklinit", False
            yield "numpy.compat", False
            yield "numpy.lib", False
            yield "numpy.linalg", False
            yield "numpy.fft", False
            yield "numpy.polynomial", False
            yield "numpy.random", False
            yield "numpy.ctypeslib", False
            yield "numpy.ma", False
            yield "numpy.matrixlib", False

        elif full_name == "numpy.core":
            yield "numpy.core._dtype_ctypes", False
            yield "numpy.core._multiarray_tests", False

        elif full_name == "numpy.random":
            # These are post-1.18 names. TODO: Once we detect versions of packages, be proper selective here.
            yield "numpy.random._bit_generator", False
            yield "numpy.random._bounded_integers", False
            yield "numpy.random._common", False
            yield "numpy.random._generator", False
            yield "numpy.random._mt19937", False
            yield "numpy.random._pcg64", False
            yield "numpy.random._philox", False
            yield "numpy.random._sfc64", False

            # These are pre-1.18 names
            yield "numpy.random.bit_generator", False
            yield "numpy.random.bounded_integers", False
            yield "numpy.random.common", False
            yield "numpy.random.generator", False
            yield "numpy.random.mt19937", False
            yield "numpy.random.pcg64", False
            yield "numpy.random.philox", False
            yield "numpy.random.sfc64", False

            # TODO: Clarify if entropy is needed for 1.18 or at all.
            yield "numpy.random.entropy", False
            yield "numpy.random.mtrand", False

        # matplotlib imports --------------------------------------------------
        elif full_name == "matplotlib":
            yield "matplotlib.backend_managers", True
            yield "matplotlib.backend_bases", True
            yield "mpl_toolkits", False

        elif full_name == "matplotlib.backends":
            yield "matplotlib.backends._backend_agg", False
            yield "matplotlib.backends._tkagg", False
            yield "matplotlib.backends.backend_tkagg", False
            yield "matplotlib.backends.backend_agg", False

        elif full_name.startswith("matplotlib.backends.backend_wx"):
            yield "matplotlib.backends.backend_wx", True
            yield "matplotlib.backends.backend_wxagg", True
            yield "wx", True

        elif full_name == "matplotlib.backends.backend_cairo":
            yield "cairo", False
            yield "cairocffi", False

        elif full_name.startswith("matplotlib.backends.backend_gtk3"):
            yield "matplotlib.backends.backend_gtk3", True
            yield "matplotlib.backends.backend_gtk3agg", True
            yield "gi", True

        elif full_name.startswith("matplotlib.backends.backend_web"):
            yield "matplotlib.backends.backend_webagg", True
            yield "matplotlib.backends.backend_webagg_core", True
            yield "tornado", True

        elif full_name.startswith("matplotlib.backends.backend_qt4"):
            yield "matplotlib.backends.backend_qt4agg", True
            yield "matplotlib.backends.backend_qt4", True
            yield "PyQt4", True

        elif full_name.startswith("matplotlib.backends.backend_qt5"):
            yield "matplotlib.backends.backend_qt5agg", True
            yield "matplotlib.backends.backend_qt5", True
            yield "PyQt5", True

        # scipy imports -------------------------------------------------------
        elif full_name == "scipy.special":
            yield "scipy.special._ufuncs_cxx", False
        elif full_name == "scipy.linalg":
            yield "scipy.linalg.cython_blas", False
            yield "scipy.linalg.cython_lapack", False
        elif full_name == "scipy.sparse.csgraph":
            yield "scipy.sparse.csgraph._validation", False
        elif full_name == "scipy._lib":
            yield "scipy._lib.messagestream", False

        # scipy imports -------------------------------------------------------
        elif full_name == "statsmodels.nonparametric":
            yield "statsmodels.nonparametric.linbin", False
            yield "statsmodels.nonparametric._smoothers_lowess", False

        elif full_name == "statsmodels.tsa":
            yield "statsmodels.tsa._exponential_smoothers", False

        elif full_name == "statsmodels.tsa.innovations":
            yield "statsmodels.tsa.innovations._arma_innovations", False

        elif full_name == "statsmodels.tsa.kalmanf":
            yield "statsmodels.tsa.kalmanf.kalman_loglike", False

        elif full_name == "statsmodels.tsa.regime_switching":
            yield "statsmodels.tsa.regime_switching._hamilton_filter", False
            yield "statsmodels.tsa.regime_switching._kim_smoother", False

        elif full_name == "statsmodels.tsa.statespace":
            yield "statsmodels.tsa.statespace._filters", False
            yield "statsmodels.tsa.statespace._initialization", False
            yield "statsmodels.tsa.statespace._kalman_filter", False
            yield "statsmodels.tsa.statespace._kalman_smoother", False
            yield "statsmodels.tsa.statespace._representation", False
            yield "statsmodels.tsa.statespace._simulation_smoother", False
            yield "statsmodels.tsa.statespace._smoothers", False
            yield "statsmodels.tsa.statespace._tools", False

        elif full_name == "statsmodels.tsa.statespace._filters":
            yield "statsmodels.tsa.statespace._filters._conventional", False
            yield "statsmodels.tsa.statespace._filters._inversions", False
            yield "statsmodels.tsa.statespace._filters._univariate", False
            yield "statsmodels.tsa.statespace._filters._univariate_diffuse", False

        elif full_name == "statsmodels.tsa.statespace._smoothers":
            yield "statsmodels.tsa.statespace._smoothers._alternative", False
            yield "statsmodels.tsa.statespace._smoothers._classical", False
            yield "statsmodels.tsa.statespace._smoothers._conventional", False
            yield "statsmodels.tsa.statespace._smoothers._univariate", False
            yield "statsmodels.tsa.statespace._smoothers._univariate_diffuse", False

        # pywt imports -----------------------------------------------
        elif full_name == "pywt":
            yield "pywt._extensions", False
        elif full_name == "pywt._extensions":
            yield "pywt._extensions._cwt", False
            yield "pywt._extensions._dwt", False
            yield "pywt._extensions._pywt", False
            yield "pywt._extensions._swt", False

        # imageio imports -----------------------------------------------
        elif full_name == "imageio":
            yield "PIL.BlpImagePlugin", False
            yield "PIL.BmpImagePlugin", False
            yield "PIL.BufrStubImagePlugin", False
            yield "PIL.CurImagePlugin", False
            yield "PIL.DcxImagePlugin", False
            yield "PIL.DdsImagePlugin", False
            yield "PIL.EpsImagePlugin", False
            yield "PIL.FitsStubImagePlugin", False
            yield "PIL.FliImagePlugin", False
            yield "PIL.FpxImagePlugin", False
            yield "PIL.FtexImagePlugin", False
            yield "PIL.GbrImagePlugin", False
            yield "PIL.GifImagePlugin", False
            yield "PIL.GribStubImagePlugin", False
            yield "PIL.Hdf5StubImagePlugin", False
            yield "PIL.IcnsImagePlugin", False
            yield "PIL.IcoImagePlugin", False
            yield "PIL.ImImagePlugin", False
            yield "PIL.ImtImagePlugin", False
            yield "PIL.IptcImagePlugin", False
            yield "PIL.Jpeg2KImagePlugin", False
            yield "PIL.JpegImagePlugin", False
            yield "PIL.McIdasImagePlugin", False
            yield "PIL.MicImagePlugin", False
            yield "PIL.MpegImagePlugin", False
            yield "PIL.MpoImagePlugin", False
            yield "PIL.MspImagePlugin", False
            yield "PIL.PalmImagePlugin", False
            yield "PIL.PcdImagePlugin", False
            yield "PIL.PcxImagePlugin", False
            yield "PIL.PdfImagePlugin", False
            yield "PIL.PixarImagePlugin", False
            yield "PIL.PngImagePlugin", False
            yield "PIL.PpmImagePlugin", False
            yield "PIL.PsdImagePlugin", False
            yield "PIL.SgiImagePlugin", False
            yield "PIL.SpiderImagePlugin", False
            yield "PIL.SunImagePlugin", False
            yield "PIL.TgaImagePlugin", False
            yield "PIL.TiffImagePlugin", False
            yield "PIL.WebPImagePlugin", False
            yield "PIL.WmfImagePlugin", False
            yield "PIL.XbmImagePlugin", False
            yield "PIL.XpmImagePlugin", False
            yield "PIL.XVThumbImagePlugin", False

        # scikit-image imports -----------------------------------------------
        elif full_name == "skimage.draw":
            yield "skimage.draw._draw", False

        elif full_name == "skimage.external.tifffile":
            yield "skimage.external.tifffile._tifffile", False

        elif full_name == "skimage.feature":
            yield "skimage.feature.brief_cy", False
            yield "skimage.feature.censure_cy", False
            yield "skimage.feature.corner_cy", False
            yield "skimage.feature.orb_cy", False
            yield "skimage.feature._cascade", False
            yield "skimage.feature._haar", False
            yield "skimage.feature._hessian_det_appx", False
            yield "skimage.feature._hoghistogram", False
            yield "skimage.feature._texture", False

        elif full_name == "skimage.filters.rank":
            yield "skimage.filters.rank.bilateral_cy", False
            yield "skimage.filters.rank.core_cy", False
            yield "skimage.filters.rank.generic_cy", False
            yield "skimage.filters.rank.percentile_cy", False

        elif full_name == "skimage.future.graph":
            yield "skimage.future.graph._ncut_cy", False

        elif full_name == "skimage.graph":
            yield "skimage.graph.heap", False
            yield "skimage.graph._mcp", False
            yield "skimage.graph._spath", False

        elif full_name == "skimage.io":
            yield "skimage.io._plugins", False

        elif full_name == "skimage.io._plugins":
            yield "skimage.io._plugins._colormixer", False
            yield "skimage.io._plugins._histograms", False
            yield "skimage.io._plugins.fits_plugin", False
            yield "skimage.io._plugins.gdal_plugin", False
            yield "skimage.io._plugins.gtk_plugin", False
            yield "skimage.io._plugins.imageio_plugin", False
            yield "skimage.io._plugins.imread_plugin", False
            yield "skimage.io._plugins.matplotlib_plugin", False
            yield "skimage.io._plugins.pil_plugin", False
            yield "skimage.io._plugins.qt_plugin", False
            yield "skimage.io._plugins.simpleitk_plugin", False
            yield "skimage.io._plugins.skivi_plugin", False
            yield "skimage.io._plugins.tifffile_plugin", False
            yield "skimage.io._plugins.util", False

        elif full_name == "skimage.measure":
            yield "skimage.measure._ccomp", False
            yield "skimage.measure._find_contours_cy", False
            yield "skimage.measure._marching_cubes_classic_cy", False
            yield "skimage.measure._marching_cubes_lewiner_cy", False
            yield "skimage.measure._moments_cy", False
            yield "skimage.measure._pnpoly", False

        elif full_name == "skimage.morphology":
            yield "skimage.morphology._convex_hull", False
            yield "skimage.morphology._extrema_cy", False
            yield "skimage.morphology._flood_fill_cy", False
            yield "skimage.morphology._greyreconstruct", False
            yield "skimage.morphology._max_tree", False
            yield "skimage.morphology._skeletonize_3d_cy", False
            yield "skimage.morphology._skeletonize_cy", False
            yield "skimage.morphology._watershed", False

        elif full_name == "skimage.restoration":
            yield "skimage.restoration._denoise_cy", False
            yield "skimage.restoration._nl_means_denoising", False
            yield "skimage.restoration._unwrap_1d", False
            yield "skimage.restoration._unwrap_2d", False
            yield "skimage.restoration._unwrap_3d", False

        elif full_name == "skimage.segmentation":
            yield "skimage.segmentation._felzenszwalb_cy", False
            yield "skimage.segmentation._quickshift_cy", False
            yield "skimage.segmentation._slic", False

        elif full_name == "skimage.transform":
            yield "skimage.transform._hough_transform", False
            yield "skimage.transform._radon_transform", False
            yield "skimage.transform._warps_cy", False

        elif full_name == "skimage._shared":
            yield "skimage._shared.geometry", False
            yield "skimage._shared.interpolation", False
            yield "skimage._shared.transform", False

        # scikit-learn imports ------------------------------------------------
        elif full_name == "sklearn.cluster":
            yield "sklearn.cluster._dbscan_inner", False
            yield "sklearn.cluster._hierarchical", False
            yield "sklearn.cluster._k_means", False
            yield "sklearn.cluster._k_means_elkan", False

        elif full_name == "sklearn.datasets":
            yield "sklearn.datasets._svmlight_format", False

        elif full_name == "sklearn.decomposition":
            yield "sklearn.decomposition.cdnmf_fast", False
            yield "sklearn.decomposition._online_lda", False

        elif full_name == "sklearn.ensemble":
            yield "sklearn.ensemble._gradient_boosting", False

        elif full_name == "sklearn.externals":
            yield "sklearn.externals.joblib", False

        elif full_name == "sklearn.externals.joblib":
            yield "sklearn.externals.joblib.numpy_pickle", False

        elif full_name == "sklearn.ensemble._hist_gradient_boosting":
            yield "sklearn.ensemble._hist_gradient_boosting.histogram", False
            yield "sklearn.ensemble._hist_gradient_boosting.splitting", False
            yield "sklearn.ensemble._hist_gradient_boosting.types", False
            yield "sklearn.ensemble._hist_gradient_boosting.utils", False
            yield "sklearn.ensemble._hist_gradient_boosting._binning", False
            yield "sklearn.ensemble._hist_gradient_boosting._gradient_boosting", False
            yield "sklearn.ensemble._hist_gradient_boosting._loss", False
            yield "sklearn.ensemble._hist_gradient_boosting._predictor", False

        elif full_name == "sklearn.feature_extraction":
            yield "sklearn.feature_extraction._hashing", False

        elif full_name == "sklearn.linear_model":
            yield "sklearn.linear_model.cd_fast", False
            yield "sklearn.linear_model.sag_fast", False
            yield "sklearn.linear_model.sgd_fast", False

        elif full_name == "sklearn.manifold":
            yield "sklearn.manifold._barnes_hut_tsne", False
            yield "sklearn.manifold._utils", False

        elif full_name == "sklearn.metrics":
            yield "sklearn.metrics.pairwise_fast", False

        elif full_name == "sklearn.metrics.cluster":
            yield "sklearn.metrics.cluster.expected_mutual_info_fast", False

        elif full_name == "sklearn.neighbors":
            yield "sklearn.neighbors.ball_tree", False
            yield "sklearn.neighbors.dist_metrics", False
            yield "sklearn.neighbors.kd_tree", False
            yield "sklearn.neighbors.quad_tree", False
            yield "sklearn.neighbors.typedefs", False

        elif full_name == "sklearn.preprocessing":
            yield "sklearn.preprocessing._csr_polynomial_expansion", False

        elif full_name == "sklearn.svm":
            yield "sklearn.svm.liblinear", False
            yield "sklearn.svm.libsvm", False
            yield "sklearn.svm.libsvm_sparse", False

        elif full_name == "sklearn.tree":
            yield "sklearn.tree._criterion", False
            yield "sklearn.tree._splitter", False
            yield "sklearn.tree._tree", False
            yield "sklearn.tree._utils", False

        elif full_name == "sklearn.utils":
            yield "sklearn.utils.arrayfuncs", False
            yield "sklearn.utils.fast_dict", False
            yield "sklearn.utils.graph_shortest_path", False
            yield "sklearn.utils.lgamma", False
            yield "sklearn.utils.murmurhash", False
            yield "sklearn.utils.seq_dataset", False
            yield "sklearn.utils.sparsefuncs_fast", False
            yield "sklearn.utils.weight_vector", False
            yield "sklearn.utils._cython_blas", False
            yield "sklearn.utils._logistic_sigmoid", False
            yield "sklearn.utils._random", False

        elif full_name == "sklearn.utils.sparsetools":
            yield "sklearn.utils.sparsetools._graph_validation", True
            yield "sklearn.utils.sparsetools._graph_tools", True
        # end of scikit-learn imports -----------------------------------------

        elif full_name == "PIL._imagingtk":
            yield "PIL._tkinter_finder", True

        elif full_name == "pkg_resources._vendor.packaging":
            yield "pkg_resources._vendor.packaging.version", True
            yield "pkg_resources._vendor.packaging.specifiers", True
            yield "pkg_resources._vendor.packaging.requirements", True

        # pendulum imports -- START -------------------------------------------
        elif full_name == "pendulum.locales":
            # TODO: This is more something for pkgutil.iter_modules that does this.
            locales_dir = os.path.join(package_dir, "locales")
            idioms = os.listdir(locales_dir)
            for idiom in idioms:
                if (
                    not os.path.isdir(os.path.join(locales_dir, idiom))
                    or idiom == "__pycache__"
                ):
                    continue
                yield "pendulum.locales." + idiom, False

        elif (
            full_name.startswith("pendulum.locales.") and elements[2] != "locale"
        ):  # only need the idiom folders
            yield "pendulum.locales." + elements[2], False
            yield "pendulum.locales." + elements[2] + ".locale", False
        # pendulum imports -- STOP --------------------------------------------

        # urllib3 -------------------------------------------------------------
        elif full_name.startswith(
            ("urllib3", "requests.packages", "requests_toolbelt._compat")
        ):
            yield "urllib3", False
            yield "urllib3._collections", False
            yield "urllib3.connection", False
            yield "urllib3.connection.appengine", False
            yield "urllib3.connectionpool", False
            yield "urllib3.contrib", False
            yield "urllib3.contrib.appengine", False
            yield "urllib3.exceptions", False
            yield "urllib3.fields", False
            yield "urllib3.filepost", False
            yield "urllib3.packages", False
            yield "urllib3.packages.six", False
            yield "urllib3.packages.ssl_match_hostname", False
            yield "urllib3.poolmanager", False
            yield "urllib3.request", False
            yield "urllib3.response", False
            yield "urllib3.util", False
            yield "urllib3.util.connection", False
            yield "urllib3.util.queue", False
            yield "urllib3.util.request", False
            yield "urllib3.util.response", False
            yield "urllib3.util.retry", False
            yield "urllib3.util.ssl_", False
            yield "urllib3.util.timeout", False
            yield "urllib3.util.url", False
            yield "urllib3.util.wait", False
            yield "urllib.error", False
            yield "urllib.parse", False
            yield "urllib.request", False
            yield "urllib.response", False

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
        elif full_name == "flask.app":
            yield "jinja2.ext"
            yield "jinja2.ext.autoescape"
            yield "jinja2.ext.with_"

        # Support for both pycryotodome (module name Crypto) and pycyptodomex (module name Cryptodome)
        elif elements[0] in ("Crypto", "Cryptodome"):
            crypto_module_name = elements[0]

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

    def getImportsByFullname(self, full_name, package_dir):
        """ Recursively create a set of imports for a fullname.

        Notes:
            If an imported item has imported kids, call me again with each kid,
            resulting in a leaf-only set (no more consequential kids).
        """
        result = OrderedSet()

        def checkImportsRecursive(module_name, package_dir):
            for item in self._getImportsByFullname(module_name, package_dir):
                if item not in result:
                    result.add(item)
                    checkImportsRecursive(item[0], package_dir)

        checkImportsRecursive(full_name, package_dir)

        return result

    def getImplicitImports(self, module):
        # Many variables, branches, due to the many cases, pylint: disable=too-many-branches
        full_name = module.getFullName()
        elements = full_name.split(".")
        module_dir = module.getCompileTimeDirectory()
        package_dir = remove_suffix(module_dir, elements[0])

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
            for item in self.getImportsByFullname(full_name, package_dir):
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
        "requests.packages.chardet": "chardet",
        "requests.packages.idna": "idna",
        "requests.packages.urllib3": "urllib3",
        "requests.packages.urllib3._collections": "urllib3._collections",
        "requests.packages.urllib3.connection": "urllib3.connection",
        "requests.packages.urllib3.connectionpool": "urllib3.connectionpool",
        "requests.packages.urllib3.contrib": "urllib3.contrib",
        "requests.packages.urllib3.contrib.appengine": "urllib3.contrib.appengine",
        "requests.packages.urllib3.contrib.ntlmpool": "urllib3.contrib.ntlmpool",
        "requests.packages.urllib3.contrib.pyopenssl": "urllib3.contrib.pyopenssl",
        "requests.packages.urllib3.contrib.socks": "urllib3.contrib.socks",
        "requests.packages.urllib3.exceptions": "urllib3.exceptions",
        "requests.packages.urllib3.fields": "urllib3.fields",
        "requests.packages.urllib3.filepost": "urllib3.filepost",
        "requests.packages.urllib3.packages": "urllib3.packages",
        "requests.packages.urllib3.packages.ordered_dict": "urllib3.packages.ordered_dict",
        "requests.packages.urllib3.packages.ssl_match_hostname": "urllib3.packages.ssl_match_hostname",
        "requests.packages.urllib3.packages.ssl_match_hostname._implementation": "urllib3.packages.ssl_match_hostname._implementation",
        "requests.packages.urllib3.poolmanager": "urllib3.poolmanager",
        "requests.packages.urllib3.request": "urllib3.request",
        "requests.packages.urllib3.response": "urllib3.response",
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
        elif full_name == "gi._gi":
            gtk_dll_path = locateDLL("gtk-3")
            dist_dll_path = os.path.join(dist_dir, os.path.basename(gtk_dll_path))
            shutil.copy(gtk_dll_path, dist_dll_path)

            return ((gtk_dll_path, dist_dll_path, None),)
        elif full_name in ("win32api", "pythoncom") and isWin32Windows():
            # Singleton, pylint: disable=global-statement
            global _added_pywin32

            result = []
            pywin_dir = getPyWin32Dir()

            if pywin_dir is not None and not _added_pywin32:
                _added_pywin32 = True

                for dll_name in "pythoncom", "pywintypes":

                    pythoncom_filename = "%s%d%d.dll" % (
                        dll_name,
                        sys.version_info[0],
                        sys.version_info[1],
                    )
                    pythoncom_dll_path = os.path.join(pywin_dir, pythoncom_filename)
                    dist_dll_path = os.path.join(dist_dir, pythoncom_filename)

                    if os.path.exists(pythoncom_dll_path):
                        shutil.copy(pythoncom_dll_path, dist_dir)

                        result.append((pythoncom_dll_path, dist_dll_path, None))

            return result

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
