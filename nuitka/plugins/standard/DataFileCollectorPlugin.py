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
""" Standard plug-in to find data files.

"""

import collections
import os

from nuitka import Options
from nuitka.__past__ import basestring  # pylint: disable=I0021,redefined-builtin
from nuitka.containers.oset import OrderedSet
from nuitka.freezer.IncludedDataFiles import (
    makeIncludedDataDirectory,
    makeIncludedDataFile,
    makeIncludedEmptyDirectories,
)
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.FileOperations import (
    getFileList,
    resolveShellPatternToFilenames,
)


def _createEmptyDirText(filename):
    # We create the same content all the time, pylint: disable=unused-argument
    return ""


def _getSubDirectoryFolders(module, subdirs):
    """Get dirnames in given subdirs of the module.

    Notes:
        All dirnames in folders below one of the subdirs are recursively
        retrieved and returned shortened to begin with the string of subdir.
    Args:
        module: module object
        subdirs: sub folder name(s) - str or None or tuple
    Returns:
        makeIncludedEmptyDirectories of found dirnames.
    """

    module_dir = module.getCompileTimeDirectory()
    file_list = []

    if subdirs is None:
        data_dirs = [module_dir]
    elif isinstance(subdirs, basestring):
        data_dirs = [os.path.join(module_dir, subdirs)]
    else:
        data_dirs = [os.path.join(module_dir, subdir) for subdir in subdirs]

    # Gather the full file list, probably makes no sense to include bytecode files
    file_list = sum(
        (
            getFileList(
                data_dir, ignore_dirs=("__pycache__",), ignore_suffixes=(".pyc",)
            )
            for data_dir in data_dirs
        ),
        [],
    )

    if not file_list:
        msg = "No files or folders found for '%s' in subfolder(s) %r (%r)." % (
            module.getFullName(),
            subdirs,
            data_dirs,
        )
        NuitkaPluginDataFileCollector.warning(msg)

    is_package = module.isCompiledPythonPackage() or module.isUncompiledPythonPackage()

    # We need to preserve the package target path in the dist folder.
    if is_package:
        package_part = module.getFullName().asPath()
    else:
        package = module.getFullName().getPackageName()

        if package is None:
            package_part = ""
        else:
            package_part = package.asPath()

    item_set = OrderedSet()

    for f in file_list:
        target = os.path.join(package_part, os.path.relpath(f, module_dir))

        dir_name = os.path.dirname(target)
        item_set.add(dir_name)

    return makeIncludedEmptyDirectories(
        source_path=module_dir,
        dest_paths=item_set,
        reason="Subdirectories of module %s" % module.getFullName(),
    )


class NuitkaPluginDataFileCollector(NuitkaPluginBase):
    plugin_name = "data-files"

    KnownDataFileDesc = collections.namedtuple(
        "KnownDataFileDesc", ("dest_path", "filename_pattern")
    )

    known_data_files = {
        # Key is the package name to trigger it
        # Value is a tuple of 2 element tuples, thus trailing commas, where
        # the target path can be specified (None is just default, i.e. the
        # package directory) and the filename relative to the source package
        # directory
        "botocore": (KnownDataFileDesc(filename_pattern="cacert.pem", dest_path=None),),
        "site": (
            KnownDataFileDesc(filename_pattern="orig-prefix.txt", dest_path=None),
        ),
        "nose.core": (KnownDataFileDesc(filename_pattern="usage.txt", dest_path=None),),
        "scrapy": (KnownDataFileDesc(filename_pattern="VERSION", dest_path=None),),
        "dask": (KnownDataFileDesc(filename_pattern="dask.yaml", dest_path=""),),
        "cairocffi": (KnownDataFileDesc(filename_pattern="VERSION", dest_path=None),),
        "cairosvg": (KnownDataFileDesc(filename_pattern="VERSION", dest_path=None),),
        "weasyprint": (KnownDataFileDesc(filename_pattern="VERSION", dest_path=None),),
        "tinycss2": (KnownDataFileDesc(filename_pattern="VERSION", dest_path=None),),
        "certifi": (KnownDataFileDesc(filename_pattern="cacert.pem", dest_path=None),),
        "importlib_resources": (
            KnownDataFileDesc(filename_pattern="version.txt", dest_path=None),
        ),
        "moto": (
            KnownDataFileDesc(
                filename_pattern="ec2/resources/instance_types.json", dest_path=None
            ),
            KnownDataFileDesc(
                filename_pattern="ec2/resources/amis.json", dest_path=None
            ),
        ),
        "skimage": (
            # TODO: Probably should use *.ini with patterns being supported.
            KnownDataFileDesc(
                filename_pattern="io/_plugins/fits_plugin.ini", dest_path=None
            ),
            KnownDataFileDesc(
                filename_pattern="io/_plugins/gdal_plugin.ini", dest_path=None
            ),
            KnownDataFileDesc(
                filename_pattern="io/_plugins/gtk_plugin.ini", dest_path=None
            ),
            KnownDataFileDesc(
                filename_pattern="io/_plugins/imageio_plugin.ini", dest_path=None
            ),
            KnownDataFileDesc(
                filename_pattern="io/_plugins/imread_plugin.ini", dest_path=None
            ),
            KnownDataFileDesc(
                filename_pattern="io/_plugins/matplotlib_plugin.ini", dest_path=None
            ),
            KnownDataFileDesc(
                filename_pattern="io/_plugins/pil_plugin.ini", dest_path=None
            ),
            KnownDataFileDesc(
                filename_pattern="io/_plugins/qt_plugin.ini", dest_path=None
            ),
            KnownDataFileDesc(
                filename_pattern="io/_plugins/simpleitk_plugin.ini", dest_path=None
            ),
            KnownDataFileDesc(
                filename_pattern="io/_plugins/tifffile_plugin.ini", dest_path=None
            ),
        ),
        "skimage.feature._orb_descriptor_positions": (
            KnownDataFileDesc(
                filename_pattern="orb_descriptor_positions.txt", dest_path=None
            ),
        ),
        "tzdata": (KnownDataFileDesc(filename_pattern="zones", dest_path=None),),
        "lib2to3.pgen2": (
            KnownDataFileDesc(filename_pattern="../*.pickle", dest_path="lib2to3"),
        ),
    }

    # data files to be copied are contained in subfolders named as the second item
    known_data_dirs = {
        "botocore": "data",
        "boto3": "data",
        "sklearn.datasets": ("data", "descr"),
        "osgeo": "data",
        "pyphen": "dictionaries",
        "pytz": "zoneinfo",
        "pytzdata": "zoneinfo",
        "tzdata": "zoneinfo",
        "pywt": "data",
        "skimage": "data",
        "weasyprint": "css",
        "xarray": "static",
        "gooey": ("languages", "images"),
        "jsonschema": "schemas",
    }

    known_data_dir_structure = {
        "pendulum": "locales",
    }

    generated_data_files = {
        "Cryptodome.Util._raw_api": (
            ("Cryptodome/Util", ".keep_dir.txt", _createEmptyDirText),
        ),
        "Crypto.Util._raw_api": (
            ("Crypto/Util", ".keep_dir.txt", _createEmptyDirText),
        ),
    }

    @classmethod
    def isRelevant(cls):
        return Options.isStandaloneMode()

    @staticmethod
    def isAlwaysEnabled():
        return True

    def considerDataFiles(self, module):
        # Many cases to deal with, pylint: disable=too-many-branches

        module_name = module.getFullName()
        module_folder = module.getCompileTimeDirectory()

        if module_name in self.known_data_files:
            for know_data_file_desc in self.known_data_files[module_name]:
                target_dir = know_data_file_desc.dest_path
                filename_pattern = know_data_file_desc.filename_pattern

                if target_dir is None:
                    if (
                        module.isCompiledPythonPackage()
                        or module.isUncompiledPythonPackage()
                    ):
                        target_dir = module_name.asPath()
                    else:
                        package_name = module_name.getPackageName()

                        if package_name is not None:
                            target_dir = module_name.getPackageName().asPath()
                        else:
                            target_dir = "."

                source_path_pattern = os.path.join(module_folder, filename_pattern)

                for filename in resolveShellPatternToFilenames(source_path_pattern):
                    yield makeIncludedDataFile(
                        source_path=filename,
                        dest_path=os.path.normpath(
                            os.path.join(target_dir, os.path.basename(filename))
                        ),
                        reason="package data for %r" % module_name.asString(),
                    )

        if module_name in self.known_data_dirs:
            data_dirs = self.known_data_dirs[module_name]

            if type(data_dirs) is not tuple:
                data_dirs = (data_dirs,)

            for data_dir in data_dirs:
                yield makeIncludedDataDirectory(
                    source_path=os.path.join(module_folder, data_dir),
                    dest_path=os.path.join(module_name.asPath(), data_dir),
                    reason="package data directory for %r" % module_name.asString(),
                )

        if module_name in self.known_data_dir_structure:
            empty_dirs = self.known_data_dir_structure[module_name]

            yield _getSubDirectoryFolders(module, empty_dirs)

        if module_name in self.generated_data_files:
            for target_dir, filename, func in self.generated_data_files[module_name]:
                if target_dir is None:
                    target_dir = module_name.replace(".", os.path.sep)

                yield (func, os.path.normpath(os.path.join(target_dir, filename)))
