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
""" Standard plug-in to find data files.

"""

import os

from nuitka import Options
from nuitka.__past__ import basestring  # pylint: disable=I0021,redefined-builtin
from nuitka.containers.oset import OrderedSet
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.FileOperations import getFileList, listDir


def _createEmptyDirText(filename):
    # We create the same content all the time, pylint: disable=unused-argument
    return ""


def _createEmptyDirNone(filename):
    # Returning None means no file creation should happen, pylint: disable=unused-argument
    return None


def remove_suffix(string, suffix):
    """Remove 'suffix' from 'string'."""
    # Special case: if suffix is empty, string[:0] returns ''. So, test
    # for a non-empty suffix.
    if suffix and string.endswith(suffix):
        return string[: -len(suffix)]
    else:
        return string


def get_package_paths(package):
    """Return the path to the package.

    Args:
        package: (str) package name
    Returns:
        tuple: (prefix, prefix/package)
    """
    import pkgutil

    loader = pkgutil.find_loader(package)
    if not loader:
        return "", ""

    file_attr = loader.get_filename(package)
    if not file_attr:
        return "", ""

    pkg_dir = os.path.dirname(file_attr)
    pkg_base = remove_suffix(pkg_dir, package.replace(".", os.sep))

    return pkg_base, pkg_dir


def _getPackageFiles(module, packages, folders_only):
    """Yield all (!) filenames in given package(s).

    Notes:
        This should be required in rare occasions only. The one example I know
        is 'dns' when used by package 'eventlet'. Eventlet imports dns modules
        only to replace them with 'green' (i.e. non-blocking) counterparts.
    Args:
        module: module object
        packages: package name(s) - str or tuple
        folders_only: (bool) indicate, whether just the folder structure should
            be generated. In that case, an empty file named DUMMY will be
            placed in each of these folders.
    Yields:
        Tuples of paths (source, dest), if folders_only is False,
        else tuples (_createEmptyDirNone, dest).
    """

    # TODO: Maybe use isinstance(basestring) for this
    if not hasattr(packages, "__getitem__"):  # so should be a string type
        packages = (packages,)

    file_list = []
    item_set = OrderedSet()

    file_dirs = []

    for package in packages:
        pkg_base, pkg_dir = get_package_paths(package)  # read package folders
        if pkg_dir:
            filename_start = len(pkg_base)  # position of package name in dir
            # read out the filenames
            pkg_files = getFileList(
                pkg_dir, ignore_dirs=("__pycache__",), ignore_suffixes=(".pyc",)
            )
            file_dirs.append(pkg_dir)
            for f in pkg_files:
                file_list.append((filename_start, f))  # append to file list

    if not file_list:  #  safeguard for unexpected cases
        msg = "No files or folders found for '%s' in packages(s) '%r' (%r)." % (
            module.getFullName(),
            packages,
            file_dirs,
        )
        NuitkaPluginDataFileCollector.warning(msg)

    for filename_start, f in file_list:  # re-read the collected filenames
        target = f[filename_start:]  # make part of name
        if folders_only is False:  # normal case: indeed copy the files
            item_set.add((f, target))
        else:  # just create the empty folder structure
            item_set.add((_createEmptyDirNone, target))

    for f in item_set:
        yield f


def _getSubDirectoryFiles(module, subdirs, folders_only):
    """Yield filenames in given subdirs of the module.

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
        else tuples (_createEmptyDirNone, dest) are yielded.
    """
    module_folder = module.getCompileTimeDirectory()
    elements = module.getFullName().split(".")
    filename_start = module_folder.find(elements[0])
    file_list = []
    item_set = OrderedSet()

    if subdirs is None:
        data_dirs = [module_folder]
    elif isinstance(subdirs, basestring):
        data_dirs = [os.path.join(module_folder, subdirs)]
    else:
        data_dirs = [os.path.join(module_folder, subdir) for subdir in subdirs]

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

    for f in file_list:
        target = f[filename_start:]
        if folders_only is False:
            item_set.add((f, target))
        else:
            item_set.add((_createEmptyDirNone, target))

    for f in item_set:
        yield f


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
        "botocore": (_getSubDirectoryFiles, "data", False),
        "boto3": (_getSubDirectoryFiles, "data", False),
        "sklearn.datasets": (_getSubDirectoryFiles, ("data", "descr"), False),
        "osgeo": (_getSubDirectoryFiles, "data", False),
        "pyphen": (_getSubDirectoryFiles, "dictionaries", False),
        "pendulum": (_getSubDirectoryFiles, "locales", True),  # folder structure only
        "pytz": (_getSubDirectoryFiles, "zoneinfo", False),
        "pytzdata": (_getSubDirectoryFiles, "zoneinfo", False),
        "pywt": (_getSubDirectoryFiles, "data", False),
        "skimage": (_getSubDirectoryFiles, "data", False),
        "weasyprint": (_getSubDirectoryFiles, "css", False),
        "xarray": (_getSubDirectoryFiles, "static", False),
        "eventlet": (_getPackageFiles, ("dns",), False),  # copy other package source
        "gooey": (_getSubDirectoryFiles, ("languages", "images"), False),
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
                        target_dir = module_name.replace(".", os.path.sep)

                    yield (
                        source_path,
                        os.path.normpath(os.path.join(target_dir, filename)),
                    )

        if module_name in self.known_data_folders:
            func, subdir, folders_only = self.known_data_folders[module_name]
            for item in func(module, subdir, folders_only):
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
