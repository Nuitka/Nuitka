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
""" Standard plug-in to find data files.

"""

import os
from logging import warning

from nuitka import Options
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.FileOperations import getFileList, listDir

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
    "requests": (("certifi", "../certifi/cacert.pem"),),
    "urllib3": (("certifi", "../certifi/cacert.pem"),),
    "importlib_resources": ((None, "version.txt"),),
    "moto": (
        (None, "./ec2/resources/instance_types.json"),
        (None, "./ec2/resources/amis.json"),
    ),
    "skimage": (
        (None, "./io/_plugins/fits_plugin.ini"),
        (None, "./io/_plugins/gdal_plugin.ini"),
        (None, "./io/_plugins/gtk_plugin.ini"),
        (None, "./io/_plugins/imageio_plugin.ini"),
        (None, "./io/_plugins/imread_plugin.ini"),
        (None, "./io/_plugins/matplotlib_plugin.ini"),
        (None, "./io/_plugins/pil_plugin.ini"),
        (None, "./io/_plugins/qt_plugin.ini"),
        (None, "./io/_plugins/simpleitk_plugin.ini"),
        (None, "./io/_plugins/tifffile_plugin.ini"),
    ),
}


def _createEmptyDirText(filename):
    # We create the same content all the time, pylint: disable=unused-argument
    return ""


def _createEmptyDirNone(filename):
    # Returning None means no file creation should happen, pylint: disable=unused-argument
    return None


generated_data_files = {
    "Cryptodome.Util._raw_api": (
        ("Cryptodome/Util", ".keep_dir.txt", _createEmptyDirText),
    ),
    "Crypto.Util._raw_api": (("Crypto/Util", ".keep_dir.txt", _createEmptyDirText),),
}


def _get_subdir_files(module, subdirs, folders_only):
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
    Returns:
        Tuples of paths (source, dest) are yielded if folders_only is False,
        else tuples (_createEmptyDirNone, dest) are yielded.
    """
    module_folder = module.getCompileTimeDirectory()
    elements = module.getFullName().split(".")
    filename_start = module_folder.find(elements[0])
    file_list = []
    item_set = set()

    if subdirs is None:
        file_list = getFileList(module_folder)
    elif type(subdirs) is str:
        data_dir = os.path.join(module_folder, subdirs)
        file_list = getFileList(data_dir)
    else:
        for subdir in subdirs:
            data_dir = os.path.join(module_folder, subdir)
            file_list.extend(getFileList(data_dir))

    if file_list == []:
        msg = "No files or folders found for '%s' in subfolder(s) '%s'." % (
            module.getFullName(),
            str(subdirs),
        )
        warning(msg)
        yield ()

    for f in file_list:
        if "__pycache__" in f or f.endswith(".pyc"):  # never makes sense
            continue

        target = f[filename_start:]
        if folders_only is False:
            item_set.add((f, target))
        else:
            item_set.add((_createEmptyDirNone, target))

    for f in item_set:
        yield f


# data files contained in subfolders named as the second item
known_data_folders = {
    "botocore": (_get_subdir_files, "data", False),
    "boto3": (_get_subdir_files, "data", False),
    "matplotlib": (_get_subdir_files, "mpl-data", False),
    "sklearn.datasets": (_get_subdir_files, ("data", "descr"), False),
    "osgeo": (_get_subdir_files, "data", False),
    "pyphen": (_get_subdir_files, "dictionaries", False),
    "pendulum": (_get_subdir_files, "locales", True),
    "pytz": (_get_subdir_files, "zoneinfo", False),
    "pytzdata": (_get_subdir_files, "zoneinfo", False),
    "pywt": (_get_subdir_files, "data", False),
    "skimage": (_get_subdir_files, "data", False),
    "weasyprint": (_get_subdir_files, "css", False),
}


class NuitkaPluginDataFileCollector(NuitkaPluginBase):
    plugin_name = "data-files"

    @staticmethod
    def isRelevant():
        return Options.isStandaloneMode()

    @staticmethod
    def isAlwaysEnabled():
        return True

    def considerDataFiles(self, module):
        module_name = module.getFullName()
        module_folder = module.getCompileTimeDirectory()

        if module_name in known_data_files:
            for target_dir, filename in known_data_files[module_name]:
                source_path = os.path.join(module_folder, filename)

                if os.path.isfile(source_path):
                    if target_dir is None:
                        target_dir = module_name.replace(".", os.path.sep)

                    yield (
                        source_path,
                        os.path.normpath(os.path.join(target_dir, filename)),
                    )

        if module_name in known_data_folders:
            func, subdir, folders_only = known_data_folders[module_name]
            for item in func(module, subdir, folders_only):
                yield item

        if module_name in generated_data_files:
            for target_dir, filename, func in generated_data_files[module_name]:
                if target_dir is None:
                    target_dir = module_name.replace(".", os.path.sep)

                yield (func, os.path.normpath(os.path.join(target_dir, filename)))

        if module_name == "lib2to3.pgen2":
            for source_path, filename in listDir(os.path.join(module_folder, "..")):
                if not filename.endswith(".pickle"):
                    continue

                yield (source_path, os.path.normpath(os.path.join("lib2to3", filename)))
