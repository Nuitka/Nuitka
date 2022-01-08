#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
import sys

from nuitka.__past__ import iter_modules
from nuitka.containers.oset import OrderedSet
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.PythonVersions import python_version
from nuitka.utils.FileOperations import getFileContentByLine
from nuitka.utils.ModuleNames import ModuleName
from nuitka.utils.SharedLibraries import getPyWin32Dir
from nuitka.utils.Utils import getOS, isLinux, isMacOS, isWin32Windows
from nuitka.utils.Yaml import parsePackageYaml


class NuitkaPluginPopularImplicitImports(NuitkaPluginBase):
    plugin_name = "implicit-imports"

    def __init__(self):
        self.config = parsePackageYaml(__package__, "implicit-imports.yml")

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

            if "." in part or "*" in part:
                if current is None:
                    self.sysexit(
                        "Error, cannot use patter for first part '%s'." % pattern
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

    def _getImportsByFullname(self, full_name):
        """Provides names of modules to imported implicitly.

        Notes:
            This methods works much like 'getImplicitImports', except that it
            accepts the search argument as a string. This allows callers to
            obtain results, which cannot provide a Nuitka module object.
        """
        # Many variables, branches, due to the many cases, pylint: disable=too-many-branches,too-many-statements

        config = self.config.get(full_name)

        # Checking for config, but also allowing fall through.
        if config:
            dependencies = config.get("depends")

            if type(dependencies) is not list or not dependencies:
                self.sysexit(
                    "Error, requiring list below 'depends' entry for '%s' entry."
                    % full_name
                )

            for dependency in dependencies:
                if dependency.startswith("."):
                    dependency = full_name.getChildNamed(dependency[1:]).asString()

                if "*" in dependency or "?" in dependency:
                    for resolved in self._resolveModulePattern(dependency):
                        yield resolved
                else:
                    yield dependency

        if full_name == "sip" and python_version < 0x300:
            yield "enum"

        elif full_name == "gtk._gtk":
            yield "pangocairo"
            yield "pango"
            yield "cairo"
            yield "gio"
            yield "atk"
        elif full_name == "atk":
            yield "gobject"
        elif full_name == "gtkunixprint":
            yield "gobject"
            yield "cairo"
            yield "gtk"
        elif full_name == "pango":
            yield "gobject"
        elif full_name == "pangocairo":
            yield "pango"
            yield "cairo"
        elif full_name == "reportlab.rl_config":
            yield "reportlab.rl_settings"
        elif full_name == "socket":
            yield "_socket"
        elif full_name == "ctypes":
            yield "_ctypes"
        elif full_name == "cairo._cairo":
            yield "gi._gobject"
        elif full_name in ("Tkinter", "tkinter"):
            yield "_tkinter"
        elif full_name == "cryptography":
            yield "_cffi_backend"
        elif full_name == "bcrypt._bcrypt":
            yield "_cffi_backend"
        elif full_name == "nacl._sodium":
            yield "_cffi_backend"
        elif full_name == "brotli._brotli":
            yield "_cffi_backend"
        elif full_name == "ipcqueue":
            yield "_cffi_backend"
        elif full_name == "_dbus_glib_bindings":
            yield "_dbus_bindings"
        elif full_name == "_mysql":
            yield "_mysql_exceptions"
        elif full_name == "lxml.objectify":
            yield "lxml.etree"
        elif full_name == "_yaml":
            yield "yaml"
        elif full_name == "apt_inst":
            yield "apt_pkg"
        elif full_name == "_ruamel_yaml":
            yield "ruamel.yaml.error"

        # start of engineio imports ------------------------------------------
        elif full_name == "engineio":
            yield "engineio.async_drivers"

        elif full_name == "engineio.async_drivers":
            yield "engineio.async_drivers.aiohttp"
            yield "engineio.async_drivers.asgi"
            yield "engineio.async_drivers.eventlet"
            yield "engineio.async_drivers.gevent"
            yield "engineio.async_drivers.gevent_uwsgi"
            yield "engineio.async_drivers.sanic"
            yield "engineio.async_drivers.threading"
            yield "engineio.async_drivers.tornado"

        # start of gevent imports --------------------------------------------
        elif full_name == "gevent":
            yield "_cffi_backend"
            yield "gevent._config"
            yield "gevent.core"
            yield "gevent.resolver_thread"
            yield "gevent.resolver_ares"
            yield "gevent.socket"
            yield "gevent.threadpool"
            yield "gevent.thread"
            yield "gevent.threading"
            yield "gevent.select"
            yield "gevent.hub"
            yield "gevent.greenlet"
            yield "gevent.local"
            yield "gevent.event"
            yield "gevent.queue"
            yield "gevent.resolver"
            yield "gevent.subprocess"
            if getOS() == "Windows":
                yield "gevent.libuv"
            else:
                yield "gevent.libev"

        elif full_name == "gevent.hub":
            yield "gevent._hub_primitives"
            yield "gevent._greenlet_primitives"
            yield "gevent._hub_local"
            yield "gevent._waiter"
            yield "gevent._util"
            yield "gevent._ident"
            yield "gevent.exceptions"

        elif full_name == "gevent.libev":
            yield "gevent.libev.corecext"
            yield "gevent.libev.corecffi"
            yield "gevent.libev.watcher"

        elif full_name == "gevent.libuv":
            yield "gevent._interfaces"
            yield "gevent._ffi"
            yield "gevent.libuv.loop"
            yield "gevent.libuv.watcher"

        elif full_name == "gevent.libuv.loop":
            yield "gevent.libuv._corecffi"
            yield "gevent._interfaces"

        elif full_name == "gevent._ffi":
            yield "gevent._ffi.loop"
            yield "gevent._ffi.callback"
            yield "gevent._ffi.watcher"

        elif full_name == "gevent._waiter":
            yield "gevent.__waiter"
            yield "gevent._gevent_c_waiter"

        elif full_name == "gevent._hub_local":
            yield "gevent.__hub_local"
            yield "gevent.__greenlet_primitives"
            yield "gevent._gevent_c_hub_local"
        elif full_name == "gevent._gevent_c_hub_local":
            yield "gevent._gevent_c_greenlet_primitives"

        elif full_name == "gevent._hub_primitives":
            yield "gevent.__hub_primitives"
            yield "gevent._gevent_cgreenlet"
            yield "gevent._gevent_c_hub_primitives"

        elif full_name == "gevent.greenlet":
            yield "gevent._hub_local"
            yield "gevent._greenlet"
            yield "gevent._gevent_c_ident"

        elif full_name == "gevent._greenlet":
            yield "gevent.__ident"

        elif full_name == "gevent.monkey":
            yield "gevent.builtins"
            yield "gevent.time"
            yield "gevent.local"
            yield "gevent.ssl"
            yield "gevent.events"

        elif full_name == "gevent.resolver":
            yield "gevent.resolver.blocking"
            yield "gevent.resolver.cares"
            yield "gevent.resolver.thread"

        elif full_name == "gevent._semaphore":
            yield "gevent._abstract_linkable"
            yield "gevent.__semaphore"
            yield "gevent._gevent_c_semaphore"

        elif full_name == "gevent._abstract_linkable":
            yield "gevent.__abstract_linkable"
            yield "gevent._gevent_c_abstract_linkable"

        elif full_name == "gevent.local":
            yield "gevent._local"
            yield "gevent._gevent_clocal"

        elif full_name == "gevent.event":
            yield "gevent._event"
            yield "gevent._gevent_cevent"

        elif full_name == "gevent.queue":
            yield "gevent._queue"
            yield "gevent._gevent_cqueue"

        elif full_name == "gevent.pool":
            yield "gevent._imap"

        elif full_name == "gevent._imap":
            yield "gevent.__imap"
            yield "gevent._gevent_c_imap"
        # end of gevent imports ----------------------------------------------

        # start of tensorflow imports ----------------------------------------
        elif full_name == "tensorflow":
            yield "tensorboard"
            yield "tensorflow_estimator"

        elif full_name == "tensorflow.python":
            yield "tensorflow.python._pywrap_tensorflow_internal"
            yield "tensorflow.python.ops"
            yield "tensorflow.python.ops.cond_v2"

        elif full_name == "tensorflow.lite.python.interpreter_wrapper":
            yield "tensorflow.lite.python.interpreter_wrapper._tensorflow_wrap_interpreter_wrapper"

        elif full_name == "tensorflow.lite.python.optimize":
            yield "tensorflow.lite.python.optimize._tensorflow_lite_wrap_calibration_wrapper"

        elif full_name == "tensorflow.lite.toco.python":
            yield "tensorflow.lite.toco.python._tensorflow_wrap_toco"

        # the remaining entries are relevant non-Windows platforms only
        elif full_name.hasNamespace("tensorflow") and getOS() != "Windows":
            if (
                full_name
                == "tensorflow.include.external.protobuf_archive.python.google.protobuf.internal"
            ):
                yield "tensorflow.include.external.protobuf_archive.python.google.protobuf.internal._api_implementation"

            elif (
                full_name
                == "tensorflow.include.external.protobuf_archive.python.google.protobuf.pyext"
            ):
                yield "tensorflow.include.external.protobuf_archive.python.google.protobuf.pyext._message"

            elif full_name == "tensorflow.python.framework":
                yield "tensorflow.python.framework.fast_tensor_util"

            elif full_name == "tensorflow.compiler.tf2tensorrt":
                yield "tensorflow.compiler.tf2tensorrt._wrap_py_utils"

            elif full_name == "tensorflow.compiler.tf2tensorrt.python.ops":
                yield "tensorflow.compiler.tf2tensorrt.python.ops.libtftrt"

            elif full_name == "tensorflow.compiler.tf2xla.ops":
                yield "tensorflow.compiler.tf2xla.ops._xla_ops"

            elif full_name == "tensorflow.contrib.tensor_forest":
                yield "tensorflow.contrib.tensor_forest.libforestprotos"

            elif full_name == "tensorflow.contrib.tensor_forest.python.ops":
                yield "tensorflow.contrib.tensor_forest.python.ops._model_ops"
                yield "tensorflow.contrib.tensor_forest.python.ops._stats_ops"
                yield "tensorflow.contrib.tensor_forest.python.ops._tensor_forest_ops"

            elif full_name == "tensorflow.contrib.tensor_forest.hybrid.python.ops":
                yield "tensorflow.contrib.tensor_forest.hybrid.python.ops._training.ops"

            elif full_name == "tensorflow.contrib.resampler.python.ops":
                yield "tensorflow.contrib.resampler.python.ops._resampler_ops"

            elif full_name == "tensorflow.contrib.nearest_neighbor.python.ops":
                yield "tensorflow.contrib.nearest_neighbor.python.ops._nearest_neighbor_ops"

            elif full_name == "tensorflow.contrib.ignite":
                yield "tensorflow.contrib.ignite._ignite_ops"

            elif full_name == "tensorflow.contrib.kinesis":
                yield "tensorflow.contrib.kinesis._dataset_ops"

            elif full_name == "tensorflow.contrib.ffmpeg":
                yield "tensorflow.contrib.ffmpeg.ffmpeg"

            elif full_name == "tensorflow.contrib.framework.python.ops":
                yield "tensorflow.contrib.framework.python.ops._variable_ops"

            elif full_name == "tensorflow.contrib.text.python.ops":
                yield "tensorflow.contrib.text.python.ops._skip_gram_ops"

            elif full_name == "tensorflow.contrib.reduce_slice_ops.python.ops":
                yield "tensorflow.contrib.reduce_slice_ops.python.ops._reduce_slice_ops"

            elif full_name == "tensorflow.contrib.periodic_resample.python.ops":
                yield "tensorflow.contrib.periodic_resample.python.ops._periodic_resample_op"

            elif full_name == "tensorflow.contrib.memory_stats.python.ops":
                yield "tensorflow.contrib.memory_stats.python.ops._memory_stats_ops"

            elif full_name == "tensorflow.contrib.libsvm.python.ops":
                yield "tensorflow.contrib.libsvm.python.ops._libsvm_ops"

            elif full_name == "tensorflow.contrib.fused_conv.python.ops":
                yield "tensorflow.contrib.fused_conv.python.ops._fused_conv2d_bias_activation_op"

            elif full_name == "tensorflow.contrib.kafka":
                yield "tensorflow.contrib.kafka._dataset_ops"

            elif full_name == "tensorflow.contrib.hadoop":
                yield "tensorflow.contrib.hadoop._dataset_ops"

            elif full_name == "tensorflow.contrib.seq2seq.python.ops":
                yield "tensorflow.contrib.seq2seq.python.ops._beam_search_ops"

            elif full_name == "tensorflow.contrib.rpc.python.kernel_tests":
                yield "tensorflow.contrib.rpc.python.kernel_tests.libtestexample"

            elif full_name == "tensorflow.contrib.boosted_trees.python.ops":
                yield "tensorflow.contrib.boosted_trees.python.ops._boosted_trees_ops"

            elif full_name == "tensorflow.contrib.layers.python.ops":
                yield "tensorflow.contrib.layers.python.ops._sparse_feature_cross_op"

            elif full_name == "tensorflow.contrib.image.python.ops":
                yield "tensorflow.contrib.image.python.ops._distort_image_ops"
                yield "tensorflow.contrib.image.python.ops._image_ops"
                yield "tensorflow.contrib.image.python.ops._single_image_random_dot_stereograms"

            elif full_name == "tensorflow.contrib.factorization.python.ops":
                yield "tensorflow.contrib.factorization.python.ops._factorization_ops"

            elif full_name == "tensorflow.contrib.input_pipeline.python.ops":
                yield "tensorflow.contrib.input_pipeline.python.ops._input_pipeline_ops"

            elif full_name == "tensorflow.contrib.rnn.python.ops":
                yield "tensorflow.contrib.rnn.python.ops._gru_ops"
                yield "tensorflow.contrib.rnn.python.ops._lstm_ops"

            elif full_name == "tensorflow.contrib.bigtable.python.ops":
                yield "tensorflow.contrib.bigtable.python.ops._bigtable"
        # end of tensorflow imports -------------------------------------------

        # boto3 imports ------------------------------------------------------
        elif full_name == "boto3":
            yield "boto3.ec2"
            yield "boto3.ec2.createtags"
            yield "boto3.ec2.deletetags"
            yield "boto3.dynamodb"
            yield "boto3.s3"
            yield "boto3.s3.inject"
            yield "boto3.s3.transfer"

        # GDAL imports ------------------------------------------------------
        elif full_name == "osgeo":
            yield "osgeo._gdal"
            yield "osgeo._gdalconst"
            yield "osgeo._gdal_array"
            yield "osgeo._gnm"
            yield "osgeo._ogr"
            yield "osgeo._osr"

        # OpenCV imports ------------------------------------------------------
        elif full_name == "cv2":
            yield "numpy"
            yield "numpy.core"

        # fastapi imports ---------------------------------------------------
        elif full_name == "fastapi":
            yield "fastapi.routing"

        # pydantic imports ---------------------------------------------------
        elif full_name == "pydantic":
            yield "pydantic.typing"
            yield "pydantic.fields"
            yield "pydantic.utils"
            yield "pydantic.schema"
            yield "pydantic.env_settings"
            yield "pydantic.main"
            yield "pydantic.error_wrappers"
            yield "pydantic.validators"
            yield "pydantic.mypy"
            yield "pydantic.version"
            yield "pydantic.types"
            yield "pydantic.color"
            yield "pydantic.parse"
            yield "pydantic.json"
            yield "pydantic.datetime_parse"
            yield "pydantic.dataclasses"
            yield "pydantic.class_validators"
            yield "pydantic.networks"
            yield "pydantic.errors"

        # uvicorn imports -----------------------------------------------------
        elif full_name == "uvicorn":
            yield "uvicorn.loops"
            yield "uvicorn.lifespan"
            yield "uvicorn.protocols"
        elif full_name == "uvicorn.config":
            yield "uvicorn.logging"
        elif full_name == "uvicorn.lifespan":
            yield "uvicorn.lifespan.off"
            yield "uvicorn.lifespan.on"
        elif full_name == "uvicorn.loops":
            yield "uvicorn.loops.auto"
            yield "uvicorn.loops.uvloop"
        elif full_name == "uvicorn.protocols":
            yield "uvicorn.protocols.http"
            yield "uvicorn.protocols.websockets"
        elif full_name == "uvicorn.protocols.http":
            yield "uvicorn.protocols.http.auto"
            yield "uvicorn.protocols.http.h11_impl"
            yield "uvicorn.protocols.http.httptools_impl"
        elif full_name == "uvicorn.protocols.websockets":
            yield "uvicorn.protocols.websockets.auto"
            yield "uvicorn.protocols.websockets.websockets_impl"
            yield "uvicorn.protocols.websockets.wsproto_impl"

        # vtk imports -----------------------------------------------------
        elif full_name == "vtkmodules":
            yield "vtkmodules.all"
            yield "vtkmodules.util"

        elif full_name == "vtkmodules.util":
            yield "vtkmodules.util.misc"
            yield "vtkmodules.util.numpy_support"
            yield "vtkmodules.util.vtkAlgorithm"
            yield "vtkmodules.util.vtkConstants"
            yield "vtkmodules.util.vtkImageExportToArray"
            yield "vtkmodules.util.vtkImageImportFromArray"
            yield "vtkmodules.util.vtkMethodParser"
            yield "vtkmodules.util.vtkVariant"

        elif full_name == "vtkmodules.qt":
            yield "vtkmodules.qt.QVTKRenderWindowInteractor"

        elif full_name == "vtkmodules.tk":
            yield "vtkmodules.tk.vtkLoadPythonTkWidgets"
            yield "vtkmodules.tk.vtkTkImageViewerWidget"
            yield "vtkmodules.tk.vtkTkPhotoImage"
            yield "vtkmodules.tk.vtkTkRenderWidget"
            yield "vtkmodules.tk.vtkTkRenderWindowInteractor"

        elif full_name == "vtkmodules.wx":
            yield "vtkmodules.wx.wxVTKRenderWindow"
            yield "vtkmodules.wx.wxVTKRenderWindowInteractor"

        # chainer imports -----------------------------------------------------
        elif full_name == "chainer":
            yield "chainer.distributions"
            yield "chainer.distributions.utils"

        elif full_name == "chainer.distributions":
            yield "chainer.distributions.utils"

        # numpy imports -------------------------------------------------------
        elif full_name == "numpy":
            yield "numpy._mklinit"
            yield "numpy.compat"
            yield "numpy.lib"
            yield "numpy.linalg"
            yield "numpy.fft"
            yield "numpy.polynomial"
            yield "numpy.random"
            yield "numpy.ctypeslib"
            yield "numpy.ma"
            yield "numpy.matrixlib"

        elif full_name == "numpy.core":
            yield "numpy.core._dtype_ctypes"
            yield "numpy.core._multiarray_tests"

        elif full_name == "numpy.random":
            # These are post-1.18 names. TODO: Once we detect versions of packages, be proper selective here.
            yield "numpy.random._bit_generator"
            yield "numpy.random._bounded_integers"
            yield "numpy.random._common"
            yield "numpy.random._generator"
            yield "numpy.random._mt19937"
            yield "numpy.random._pcg64"
            yield "numpy.random._philox"
            yield "numpy.random._sfc64"

            # These are pre-1.18 names
            yield "numpy.random.bit_generator"
            yield "numpy.random.bounded_integers"
            yield "numpy.random.common"
            yield "numpy.random.generator"
            yield "numpy.random.mt19937"
            yield "numpy.random.pcg64"
            yield "numpy.random.philox"
            yield "numpy.random.sfc64"

            # TODO: Clarify if entropy is needed for 1.18 or at all.
            yield "numpy.random.entropy"
            yield "numpy.random.mtrand"

        # matplotlib imports --------------------------------------------------
        elif full_name == "matplotlib":
            yield "matplotlib.backend_managers"
            yield "matplotlib.backend_bases"
            yield "mpl_toolkits"

        elif full_name == "matplotlib.backends":
            yield "matplotlib.backends._backend_agg"
            yield "matplotlib.backends._tkagg"
            yield "matplotlib.backends.backend_tkagg"
            yield "matplotlib.backends.backend_agg"

        elif full_name.hasOneOfNamespaces(
            "matplotlib.backends.backend_wx", "matplotlib.backends.backend_wxagg"
        ):
            yield "matplotlib.backends.backend_wx"
            yield "matplotlib.backends.backend_wxagg"
            yield "wx"

        elif full_name == "matplotlib.backends.backend_cairo":
            yield "cairo"
            yield "cairocffi"

        elif full_name.hasOneOfNamespaces(
            "matplotlib.backends.backend_gtk3", "matplotlib.backends.backend_gtk3agg"
        ):
            yield "matplotlib.backends.backend_gtk3"
            yield "matplotlib.backends.backend_gtk3agg"
            yield "gi"

        elif full_name.hasOneOfNamespaces(
            "matplotlib.backends.backend_webagg",
            "matplotlib.backends.backend_webagg_core",
        ):
            yield "matplotlib.backends.backend_webagg"
            yield "matplotlib.backends.backend_webagg_core"
            yield "tornado"

        elif full_name.hasOneOfNamespaces(
            "matplotlib.backends.backend_qt5agg", "matplotlib.backends.backend_qt5"
        ):
            yield "matplotlib.backends.backend_qt5agg"
            yield "matplotlib.backends.backend_qt5"
            yield "PyQt5"

        # scipy imports -------------------------------------------------------
        elif full_name == "scipy.stats._stats":
            yield "scipy.special.cython_special"
        elif full_name == "scipy.special":
            yield "scipy.special._ufuncs_cxx"
        elif full_name == "scipy.linalg":
            yield "scipy.linalg.cython_blas"
            yield "scipy.linalg.cython_lapack"
        elif full_name == "scipy.sparse.csgraph":
            yield "scipy.sparse.csgraph._validation"
        elif full_name == "scipy._lib":
            yield "scipy._lib.messagestream"
        elif full_name == "scipy.spatial":
            yield "scipy.spatial.transform"
        elif full_name == "scipy.spatial.transform":
            yield "scipy.spatial.transform._rotation_groups"

        # statsmodels imports -------------------------------------------------------
        elif full_name == "statsmodels.nonparametric":
            yield "statsmodels.nonparametric.linbin"
            yield "statsmodels.nonparametric._smoothers_lowess"

        elif full_name == "statsmodels.tsa":
            yield "statsmodels.tsa._exponential_smoothers"

        elif full_name == "statsmodels.tsa.innovations":
            yield "statsmodels.tsa.innovations._arma_innovations"

        elif full_name == "statsmodels.tsa.kalmanf":
            yield "statsmodels.tsa.kalmanf.kalman_loglike"

        elif full_name == "statsmodels.tsa.regime_switching":
            yield "statsmodels.tsa.regime_switching._hamilton_filter"
            yield "statsmodels.tsa.regime_switching._kim_smoother"

        elif full_name == "statsmodels.tsa.statespace":
            yield "statsmodels.tsa.statespace._filters"
            yield "statsmodels.tsa.statespace._initialization"
            yield "statsmodels.tsa.statespace._kalman_filter"
            yield "statsmodels.tsa.statespace._kalman_smoother"
            yield "statsmodels.tsa.statespace._representation"
            yield "statsmodels.tsa.statespace._simulation_smoother"
            yield "statsmodels.tsa.statespace._smoothers"
            yield "statsmodels.tsa.statespace._tools"

        elif full_name == "statsmodels.tsa.statespace._filters":
            yield "statsmodels.tsa.statespace._filters._conventional"
            yield "statsmodels.tsa.statespace._filters._inversions"
            yield "statsmodels.tsa.statespace._filters._univariate"
            yield "statsmodels.tsa.statespace._filters._univariate_diffuse"

        elif full_name == "statsmodels.tsa.statespace._smoothers":
            yield "statsmodels.tsa.statespace._smoothers._alternative"
            yield "statsmodels.tsa.statespace._smoothers._classical"
            yield "statsmodels.tsa.statespace._smoothers._conventional"
            yield "statsmodels.tsa.statespace._smoothers._univariate"
            yield "statsmodels.tsa.statespace._smoothers._univariate_diffuse"

        # pywt imports -----------------------------------------------
        elif full_name == "pywt":
            yield "pywt._extensions"
        elif full_name == "pywt._extensions":
            yield "pywt._extensions._cwt"
            yield "pywt._extensions._dwt"
            yield "pywt._extensions._pywt"
            yield "pywt._extensions._swt"

        # imageio imports -----------------------------------------------
        elif full_name == "imageio":
            yield "PIL.BlpImagePlugin"
            yield "PIL.BmpImagePlugin"
            yield "PIL.BufrStubImagePlugin"
            yield "PIL.CurImagePlugin"
            yield "PIL.DcxImagePlugin"
            yield "PIL.DdsImagePlugin"
            yield "PIL.EpsImagePlugin"
            yield "PIL.FitsStubImagePlugin"
            yield "PIL.FliImagePlugin"
            yield "PIL.FpxImagePlugin"
            yield "PIL.FtexImagePlugin"
            yield "PIL.GbrImagePlugin"
            yield "PIL.GifImagePlugin"
            yield "PIL.GribStubImagePlugin"
            yield "PIL.Hdf5StubImagePlugin"
            yield "PIL.IcnsImagePlugin"
            yield "PIL.IcoImagePlugin"
            yield "PIL.ImImagePlugin"
            yield "PIL.ImtImagePlugin"
            yield "PIL.IptcImagePlugin"
            yield "PIL.Jpeg2KImagePlugin"
            yield "PIL.JpegImagePlugin"
            yield "PIL.McIdasImagePlugin"
            yield "PIL.MicImagePlugin"
            yield "PIL.MpegImagePlugin"
            yield "PIL.MpoImagePlugin"
            yield "PIL.MspImagePlugin"
            yield "PIL.PalmImagePlugin"
            yield "PIL.PcdImagePlugin"
            yield "PIL.PcxImagePlugin"
            yield "PIL.PdfImagePlugin"
            yield "PIL.PixarImagePlugin"
            yield "PIL.PngImagePlugin"
            yield "PIL.PpmImagePlugin"
            yield "PIL.PsdImagePlugin"
            yield "PIL.SgiImagePlugin"
            yield "PIL.SpiderImagePlugin"
            yield "PIL.SunImagePlugin"
            yield "PIL.TgaImagePlugin"
            yield "PIL.TiffImagePlugin"
            yield "PIL.WebPImagePlugin"
            yield "PIL.WmfImagePlugin"
            yield "PIL.XbmImagePlugin"
            yield "PIL.XpmImagePlugin"
            yield "PIL.XVThumbImagePlugin"

        # scikit-image imports -----------------------------------------------
        elif full_name == "skimage.draw":
            yield "skimage.draw._draw"

        elif full_name == "skimage.external.tifffile":
            yield "skimage.external.tifffile._tifffile"

        elif full_name == "skimage.feature.orb_cy":
            yield "skimage.feature._orb_descriptor_positions"

        elif full_name == "skimage.feature":
            yield "skimage.feature.brief_cy"
            yield "skimage.feature.censure_cy"
            yield "skimage.feature.corner_cy"
            yield "skimage.feature.orb_cy"
            yield "skimage.feature._cascade"
            yield "skimage.feature._haar"
            yield "skimage.feature._hessian_det_appx"
            yield "skimage.feature._hoghistogram"
            yield "skimage.feature._texture"

        elif full_name == "skimage.filters.rank":
            yield "skimage.filters.rank.bilateral_cy"
            yield "skimage.filters.rank.core_cy"
            yield "skimage.filters.rank.core_cy_3d"
            yield "skimage.filters.rank.generic_cy"
            yield "skimage.filters.rank.percentile_cy"

        elif full_name == "skimage.future.graph":
            yield "skimage.future.graph._ncut_cy"

        elif full_name == "skimage.graph":
            yield "skimage.graph.heap"
            yield "skimage.graph._mcp"
            yield "skimage.graph._spath"

        elif full_name == "skimage.io":
            yield "skimage.io._plugins"

        elif full_name == "skimage.io._plugins":
            yield "skimage.io._plugins._colormixer"
            yield "skimage.io._plugins._histograms"
            yield "skimage.io._plugins.fits_plugin"
            yield "skimage.io._plugins.gdal_plugin"
            yield "skimage.io._plugins.gtk_plugin"
            yield "skimage.io._plugins.imageio_plugin"
            yield "skimage.io._plugins.imread_plugin"
            yield "skimage.io._plugins.matplotlib_plugin"
            yield "skimage.io._plugins.pil_plugin"
            yield "skimage.io._plugins.qt_plugin"
            yield "skimage.io._plugins.simpleitk_plugin"
            yield "skimage.io._plugins.skivi_plugin"
            yield "skimage.io._plugins.tifffile_plugin"
            yield "skimage.io._plugins.util"

        elif full_name == "skimage.measure":
            yield "skimage.measure._ccomp"
            yield "skimage.measure._find_contours_cy"
            yield "skimage.measure._marching_cubes_classic_cy"
            yield "skimage.measure._marching_cubes_lewiner_cy"
            yield "skimage.measure._moments_cy"
            yield "skimage.measure._pnpoly"

        elif full_name == "skimage.morphology":
            yield "skimage.morphology._convex_hull"
            yield "skimage.morphology._extrema_cy"
            yield "skimage.morphology._flood_fill_cy"
            yield "skimage.morphology._greyreconstruct"
            yield "skimage.morphology._max_tree"
            yield "skimage.morphology._skeletonize_3d_cy"
            yield "skimage.morphology._skeletonize_cy"
            yield "skimage.morphology._watershed"

        elif full_name == "skimage.restoration":
            yield "skimage.restoration._denoise_cy"
            yield "skimage.restoration._nl_means_denoising"
            yield "skimage.restoration._unwrap_1d"
            yield "skimage.restoration._unwrap_2d"
            yield "skimage.restoration._unwrap_3d"

        elif full_name == "skimage.segmentation":
            yield "skimage.segmentation._felzenszwalb_cy"
            yield "skimage.segmentation._quickshift_cy"
            yield "skimage.segmentation._slic"

        elif full_name == "skimage.transform":
            yield "skimage.transform._hough_transform"
            yield "skimage.transform._radon_transform"
            yield "skimage.transform._warps_cy"

        elif full_name == "skimage._shared":
            yield "skimage._shared.geometry"
            yield "skimage._shared.interpolation"
            yield "skimage._shared.transform"

        # scikit-learn imports ------------------------------------------------
        elif full_name == "sklearn.cluster":
            yield "sklearn.cluster._dbscan_inner"
            yield "sklearn.cluster._hierarchical"
            yield "sklearn.cluster._k_means"
            yield "sklearn.cluster._k_means_elkan"

        elif full_name == "sklearn.datasets":
            yield "sklearn.datasets._svmlight_format"

        elif full_name == "sklearn.decomposition":
            yield "sklearn.decomposition.cdnmf_fast"
            yield "sklearn.decomposition._online_lda"

        elif full_name == "sklearn.ensemble":
            yield "sklearn.ensemble._gradient_boosting"

        elif full_name == "sklearn.externals":
            yield "sklearn.externals.joblib"

        elif full_name == "sklearn.externals.joblib":
            yield "sklearn.externals.joblib.numpy_pickle"

        elif full_name == "sklearn.ensemble._hist_gradient_boosting":
            yield "sklearn.ensemble._hist_gradient_boosting.histogram"
            yield "sklearn.ensemble._hist_gradient_boosting.splitting"
            yield "sklearn.ensemble._hist_gradient_boosting.types"
            yield "sklearn.ensemble._hist_gradient_boosting.utils"
            yield "sklearn.ensemble._hist_gradient_boosting._binning"
            yield "sklearn.ensemble._hist_gradient_boosting._gradient_boosting"
            yield "sklearn.ensemble._hist_gradient_boosting._loss"
            yield "sklearn.ensemble._hist_gradient_boosting._predictor"

        elif full_name == "sklearn.feature_extraction":
            yield "sklearn.feature_extraction._hashing"

        elif full_name == "sklearn.linear_model":
            yield "sklearn.linear_model.cd_fast"
            yield "sklearn.linear_model.sag_fast"
            yield "sklearn.linear_model.sgd_fast"

        elif full_name == "sklearn.manifold":
            yield "sklearn.manifold._barnes_hut_tsne"
            yield "sklearn.manifold._utils"

        elif full_name == "sklearn.metrics":
            yield "sklearn.metrics.pairwise_fast"

        elif full_name == "sklearn.metrics.cluster":
            yield "sklearn.metrics.cluster.expected_mutual_info_fast"

        elif full_name == "sklearn.neighbors":
            yield "sklearn.neighbors.ball_tree"
            yield "sklearn.neighbors.dist_metrics"
            yield "sklearn.neighbors.kd_tree"
            yield "sklearn.neighbors.quad_tree"
            yield "sklearn.neighbors.typedefs"

        elif full_name == "sklearn.preprocessing":
            yield "sklearn.preprocessing._csr_polynomial_expansion"

        elif full_name == "sklearn.svm":
            yield "sklearn.svm.liblinear"
            yield "sklearn.svm.libsvm"
            yield "sklearn.svm.libsvm_sparse"

        elif full_name == "sklearn.tree":
            yield "sklearn.tree._criterion"
            yield "sklearn.tree._splitter"
            yield "sklearn.tree._tree"
            yield "sklearn.tree._utils"

        elif full_name == "sklearn.utils":
            yield "sklearn.utils.arrayfuncs"
            yield "sklearn.utils.fast_dict"
            yield "sklearn.utils.graph_shortest_path"
            yield "sklearn.utils.lgamma"
            yield "sklearn.utils.murmurhash"
            yield "sklearn.utils.seq_dataset"
            yield "sklearn.utils.sparsefuncs_fast"
            yield "sklearn.utils.weight_vector"
            yield "sklearn.utils._cython_blas"
            yield "sklearn.utils._logistic_sigmoid"
            yield "sklearn.utils._random"

        elif full_name == "sklearn.utils.sparsetools":
            yield "sklearn.utils.sparsetools._graph_validation"
            yield "sklearn.utils.sparsetools._graph_tools"

        elif full_name == "sklearn.utils._hough_transform":
            yield "skimage.draw"
        # end of scikit-learn imports -----------------------------------------

        elif full_name == "PIL._imagingtk":
            yield "PIL._tkinter_finder"

        elif full_name == "pkg_resources._vendor.packaging":
            yield "pkg_resources._vendor.packaging.version"
            yield "pkg_resources._vendor.packaging.specifiers"
            yield "pkg_resources._vendor.packaging.requirements"

        # TODO: Is this even true, or an artifact of how we handled requests.packages.urllib3 in the past.
        # urllib3 -------------------------------------------------------------
        elif full_name in ("urllib3", "requests_toolbelt._compat"):
            yield "urllib3"
            yield "urllib3._collections"
            yield "urllib3.connection"
            yield "urllib3.connection.appengine"
            yield "urllib3.connectionpool"
            yield "urllib3.contrib"
            yield "urllib3.contrib.appengine"
            yield "urllib3.exceptions"
            yield "urllib3.fields"
            yield "urllib3.filepost"
            yield "urllib3.packages"
            yield "urllib3.packages.six"
            yield "urllib3.packages.ssl_match_hostname"
            yield "urllib3.poolmanager"
            yield "urllib3.request"
            yield "urllib3.response"
            yield "urllib3.util"
            yield "urllib3.util.connection"
            yield "urllib3.util.queue"
            yield "urllib3.util.request"
            yield "urllib3.util.response"
            yield "urllib3.util.retry"
            yield "urllib3.util.ssl_"
            yield "urllib3.util.timeout"
            yield "urllib3.util.url"
            yield "urllib3.util.wait"
            yield "urllib.error"
            yield "urllib.parse"
            yield "urllib.request"
            yield "urllib.response"

        elif full_name == "uvloop.loop":
            yield "uvloop._noop"
        elif full_name == "fitz.fitz":
            yield "fitz._fitz"
        elif full_name == "pandas._libs":
            yield "pandas._libs.tslibs.np_datetime"
            yield "pandas._libs.tslibs.nattype"
            yield "pandas._libs.tslibs.base"
        elif full_name == "pandas.core.window":
            yield "pandas._libs.window"
            yield "pandas._libs.skiplist"
        elif full_name == "pandas._libs.testing":
            yield "cmath"
        elif full_name == "flask.app":
            yield "jinja2.ext"
            yield "jinja2.ext.autoescape"
            yield "jinja2.ext.with_"

        # Support for both pycryotodome (module name Crypto) and pycyptodomex (module name Cryptodome)
        elif full_name.hasOneOfNamespaces("Crypto", "Cryptodome"):
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
            elif full_name == crypto_module_name + ".Cipher.Salsa20":
                yield crypto_module_name + ".Cipher._Salsa20"
            elif full_name == crypto_module_name + ".Cipher.ChaCha20":
                yield crypto_module_name + ".Cipher._chacha20"
            elif full_name == crypto_module_name + ".PublicKey.ECC":
                yield crypto_module_name + ".PublicKey._ec_ws"
            elif full_name == crypto_module_name + ".Cipher.ARC4":
                yield crypto_module_name + ".Cipher._ARC4"
            elif full_name == crypto_module_name + ".Math._IntegerCustom":
                yield crypto_module_name + ".Math._modexp"
        elif full_name == "pycparser.c_parser":
            yield "pycparser.yacctab"
            yield "pycparser.lextab"
        elif full_name == "passlib.hash":
            yield "passlib.handlers.sha2_crypt"
        elif full_name == "pyglet":
            yield "pyglet.app"
            yield "pyglet.canvas"
            yield "pyglet.clock"
            yield "pyglet.com"
            yield "pyglet.event"
            yield "pyglet.font"
            yield "pyglet.gl"
            yield "pyglet.graphics"
            yield "pyglet.input"
            yield "pyglet.image"
            yield "pyglet.lib"
            yield "pyglet.media"
            yield "pyglet.model"
            yield "pyglet.resource"
            yield "pyglet.sprite"
            yield "pyglet.shapes"
            yield "pyglet.text"
            yield "pyglet.window"
        elif full_name in ("pynput.keyboard", "pynput.mouse"):
            if isMacOS():
                yield full_name.getChildNamed("_darwin")
            elif isWin32Windows():
                yield full_name.getChildNamed("_win32")
            else:
                yield full_name.getChildNamed("xorg")
        elif full_name == "_pytest._code.code":
            yield "py._path.local"
        elif full_name == "pyreadstat._readstat_parser":
            yield "pandas"
        elif full_name == "pyreadstat.pyreadstat":
            yield "pyreadstat._readstat_writer"
            yield "pyreadstat.worker"
        elif full_name == "cytoolz.itertoolz":
            yield "cytoolz.utils"
        elif full_name == "cytoolz.functoolz":
            yield "cytoolz._signatures"
        elif full_name == "exchangelib":
            yield "tzdata"
        elif full_name == "curses":
            yield "_curses"
        elif full_name == "h5py.h5":
            yield "h5py.defs"
        elif full_name == "h5py.h5s":
            yield "h5py.utils"
        elif full_name == "h5py.h5p":
            yield "h5py.h5ac"
        elif full_name == "h5py.h5a":
            yield "h5py._proxy"
        elif full_name == "kivy._clock":
            yield "kivy.weakmethod"
        elif full_name == "kivy.graphics.instructions":
            yield "kivy.graphics.buffer"
            yield "kivy.graphics.vertex"
            yield "kivy.graphics.vbo"
        elif full_name == "kivy.graphics.vbo":
            yield "kivy.graphics.compiler"
        elif full_name == "kivy.graphics.compiler":
            yield "kivy.graphics.shader"
        elif full_name == "mercurial.encoding":
            yield "mercurial.charencode"
            yield "mercurial.cext.parsers"

    def getImportsByFullname(self, full_name):
        """Recursively create a set of imports for a fullname.

        Notes:
            If an imported item has imported kids, call again with each new item,
            resulting in a leaf-only set (no more consequential kids).
        """
        result = OrderedSet()

        def checkImportsRecursive(module_name):
            for item in self._getImportsByFullname(module_name):
                item = ModuleName(item)

                if item not in result:
                    result.add(item)
                    checkImportsRecursive(item)

        checkImportsRecursive(full_name)

        if full_name in result:
            result.remove(full_name)

        return result

    def getImplicitImports(self, module):
        full_name = module.getFullName()

        if module.isPythonShlibModule():
            for used_module in module.getUsedModules():
                yield used_module[0]

        if full_name == "pkg_resources.extern":
            for line in getFileContentByLine(module.getCompileTimeFilename()):
                if line.startswith("names"):
                    line = line.split("=")[-1].strip()
                    parts = line.split(",")

                    for part in parts:
                        yield "pkg_resources._vendor." + part.strip("' ")
        else:
            # create a flattened import set for full_name and yield from it
            for item in self.getImportsByFullname(full_name):
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

    def getExtraDlls(self, module):
        full_name = module.getFullName()

        if full_name == "uuid" and isLinux():
            uuid_dll_path = self.locateDLL("uuid")

            if uuid_dll_path is not None:
                yield self.makeDllEntryPoint(
                    uuid_dll_path, os.path.basename(uuid_dll_path), None
                )
        elif full_name == "iptc" and isLinux():
            import iptc.util  # pylint: disable=I0021,import-error

            xtwrapper_dll = iptc.util.find_library("xtwrapper")[0]
            xtwrapper_dll_path = xtwrapper_dll._name  # pylint: disable=protected-access

            yield self.makeDllEntryPoint(
                xtwrapper_dll_path, os.path.basename(xtwrapper_dll_path), None
            )
        elif full_name == "coincurve._libsecp256k1" and isWin32Windows():
            yield self.makeDllEntryPoint(
                os.path.join(module.getCompileTimeDirectory(), "libsecp256k1.dll"),
                os.path.join(full_name.getPackageName(), "libsecp256k1.dll"),
                full_name.getPackageName(),
            )
        # TODO: This should be its own plugin.
        elif (
            full_name
            in (
                "pythoncom",
                "win32api",
                "win32clipboard",
                "win32console",
                "win32cred",
                "win32crypt",
                "win32event",
                "win32evtlog",
                "win32file",
                "win32gui",
                "win32help",
                "win32inet",
                "win32job",
                "win32lz",
                "win32net",
                "win32pdh",
                "win32pipe",
                "win32print",
                "win32process",
                "win32profile",
                "win32ras",
                "win32security",
                "win32service",
                "win32trace",
                "win32transaction",
                "win32ts",
                "win32wnet",
            )
            and isWin32Windows()
        ):
            pywin_dir = getPyWin32Dir()

            if pywin_dir is not None:
                for dll_name in "pythoncom", "pywintypes":

                    pythoncom_filename = "%s%d%d.dll" % (
                        dll_name,
                        sys.version_info[0],
                        sys.version_info[1],
                    )
                    pythoncom_dll_path = os.path.join(pywin_dir, pythoncom_filename)

                    if os.path.exists(pythoncom_dll_path):
                        yield self.makeDllEntryPoint(
                            pythoncom_dll_path, pythoncom_filename, None
                        )

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
        "phonenumbers.geodata",  # Not performance relevant and slow C compile
        "site",  # Not performance relevant and problems with .pth files
    )

    def decideCompilation(self, module_name):
        if module_name.hasOneOfNamespaces(self.unworthy_namespaces):
            return "bytecode"
