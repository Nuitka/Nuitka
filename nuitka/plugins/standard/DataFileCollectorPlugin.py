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

import os

from nuitka import Options
from nuitka.__past__ import basestring  # pylint: disable=I0021,redefined-builtin
from nuitka.containers.oset import OrderedSet
from nuitka.freezer.IncludedDataFiles import makeIncludedEmptyDirectories
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.FileOperations import getFileList, listDir


def _createEmptyDirText(filename):
    # We create the same content all the time, pylint: disable=unused-argument
    return ""


def _getSubDirectoryFiles2(module, subdirs, folders_only):
    """Get filenames or dirnames in given subdirs of the module.

    Notes:
        All filenames in folders below one of the subdirs are recursively
        retrieved and returned shortened to begin with the string of subdir.
    Args:
        module: module object
        subdirs: sub folder name(s) - str or None or tuple
        folders_only: (bool) indicate, whether just the folder structure should
            be generated. In that case, an empty file named DUMMY will be
            placed in each of these folders.
    Yields:
        Tuples of paths (source, dest) are yielded if folders_only is False,
        else IncludedDataFile instances for empty dirs.
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

        if folders_only:
            dir_name = os.path.dirname(target)
            item_set.add(dir_name)
        else:
            item_set.add((f, target))

    if folders_only:
        return makeIncludedEmptyDirectories(
            source_path=module_dir,
            dest_paths=item_set,
            reason="Subdirectories of module %s" % module.getFullName(),
        )

    return item_set


def _getSubDirectoryFiles(module, subdirs):
    return _getSubDirectoryFiles2(module, subdirs, False)


def _getSubDirectoryFolders(module, subdirs):
    return _getSubDirectoryFiles2(module, subdirs, True)


class NuitkaPluginDataFileCollector(NuitkaPluginBase):
    plugin_name = "data-files"

    known_data_files = {
        # Key is the package name to trigger it
        # Value is a tuple of 2 element tuples, thus trailing commas, where
        # the target path can be specified (None is just default, i.e. the
        # package directory) and the filename relative to the source package
        # directory
        "botocore": ((None, "cacert.pem"),),
        "site": ((None, "orig-prefix.txt"),),
        "nose.core": ((None, "usage.txt"),),
        "scrapy": ((None, "VERSION"),),
        "dask": (("", "dask.yaml"),),
        "cairocffi": ((None, "VERSION"),),
        "cairosvg": ((None, "VERSION"),),
        "weasyprint": ((None, "VERSION"),),
        "tinycss2": ((None, "VERSION"),),
        "certifi": ((None, "cacert.pem"),),
        "importlib_resources": ((None, "version.txt"),),
        "moto": (
            (None, "ec2/resources/instance_types.json"),
            (None, "ec2/resources/amis.json"),
        ),
        "skimage": (
            (None, "io/_plugins/fits_plugin.ini"),
            (None, "io/_plugins/gdal_plugin.ini"),
            (None, "io/_plugins/gtk_plugin.ini"),
            (None, "io/_plugins/imageio_plugin.ini"),
            (None, "io/_plugins/imread_plugin.ini"),
            (None, "io/_plugins/matplotlib_plugin.ini"),
            (None, "io/_plugins/pil_plugin.ini"),
            (None, "io/_plugins/qt_plugin.ini"),
            (None, "io/_plugins/simpleitk_plugin.ini"),
            (None, "io/_plugins/tifffile_plugin.ini"),
        ),
        "skimage.feature._orb_descriptor_positions": (
            ("skimage/feature", "orb_descriptor_positions.txt"),
        ),
    }

    # data files to be copied are contained in subfolders named as the second item
    # the 3rd item indicates whether to recreate toe folder structure only (True),
    # or indeed also copy the files.
    known_data_folders = {
        "botocore": (_getSubDirectoryFiles, "data"),
        "boto3": (_getSubDirectoryFiles, "data"),
        "sklearn.datasets": (_getSubDirectoryFiles, ("data", "descr")),
        "osgeo": (_getSubDirectoryFiles, "data"),
        "pyphen": (_getSubDirectoryFiles, "dictionaries"),
        "pendulum": (_getSubDirectoryFolders, "locales"),
        "pytz": (_getSubDirectoryFiles, "zoneinfo"),
        "pytzdata": (_getSubDirectoryFiles, "zoneinfo"),
        "pywt": (_getSubDirectoryFiles, "data"),
        "skimage": (
            _getSubDirectoryFiles,
            "data",
        ),
        "weasyprint": (_getSubDirectoryFiles, "css"),
        "xarray": (_getSubDirectoryFiles, "static"),
        #        "eventlet": (_getPackageFiles, "dns"),
        "gooey": (_getSubDirectoryFiles, ("languages", "images")),
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
        module_name = module.getFullName()
        module_folder = module.getCompileTimeDirectory()

        if module_name in self.known_data_files:
            for target_dir, filename in self.known_data_files[module_name]:
                source_path = os.path.join(module_folder, filename)

                if os.path.isfile(source_path):
                    if target_dir is None:
                        target_dir = module_name.asPath()

                    yield (
                        source_path,
                        os.path.normpath(os.path.join(target_dir, filename)),
                    )

        if module_name in self.known_data_folders:
            func, subdir = self.known_data_folders[module_name]

            for item in func(module, subdir):
                yield item

        if module_name in self.generated_data_files:
            for target_dir, filename, func in self.generated_data_files[module_name]:
                if target_dir is None:
                    target_dir = module_name.replace(".", os.path.sep)

                yield (func, os.path.normpath(os.path.join(target_dir, filename)))

        if module_name == "lib2to3.pgen2":
            for source_path, filename in listDir(os.path.join(module_folder, "..")):
                if not filename.endswith(".pickle"):
                    continue

                yield (source_path, os.path.normpath(os.path.join("lib2to3", filename)))
