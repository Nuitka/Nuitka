""" This module is only an abstraction of OrderedSet which is not present in
Python at all.

spell-checker: ignore orderedset,orderedsets

"""

import os
import subprocess
import sys

from nuitka.PythonVersions import python_version
from nuitka.utils.InlineCopies import getDownloadCopyFolder

recommended_orderedset_package_name, recommended_orderedset_module_name = (
    ("ordered-set", "ordered_set")
    if python_version >= 0x370
    else ("orderedset", "orderedsets")
)


def _tryImportOrderedSet():
    try:
        from orderedset import OrderedSet as result
    except ImportError:
        try:
            from ordered_set import OrderedSet as result
        except ImportError:
            return None

    return result


OrderedSet = _tryImportOrderedSet()


def _findDownloadSitePackagesDir(download_folder):
    for root, dirnames, _filenames in os.walk(download_folder):
        found_candidate = None
        for candidate in ("site-packages", "dist-packages", "vendor-packages"):
            if candidate in dirnames:
                # Unclear which one to use.
                if found_candidate is not None:
                    return

                found_candidate = candidate

        if found_candidate:
            return os.path.join(root, found_candidate)


def tryDownloadPackageName(package_name, module_name, package_version):
    download_folder = getDownloadCopyFolder()

    site_packages_folder = _findDownloadSitePackagesDir(download_folder)

    if site_packages_folder is not None:
        candidate = os.path.join(site_packages_folder, module_name)

        if os.path.exists(candidate):
            return site_packages_folder

    if os.getenv("NUITKA_ASSUME_YES_FOR_DOWNLOADS") in ("1", "true", "yes"):
        if package_version is not None:
            package_spec = "%s==%s" % (package_name, package_version)
        else:
            package_spec = package_name

        exit_code = subprocess.call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--root",
                download_folder,
                package_spec,
            ],
            shell=False,
        )

        if exit_code != 0:
            return None

        if site_packages_folder is None:
            site_packages_folder = _findDownloadSitePackagesDir(download_folder)

    if site_packages_folder is not None:
        candidate = os.path.join(site_packages_folder, module_name)

        if os.path.exists(candidate):
            return site_packages_folder


def _tryDownloadOrderedSet():
    return tryDownloadPackageName(
        recommended_orderedset_package_name,
        recommended_orderedset_module_name,
        package_version=None,
    )


if OrderedSet is None:
    downloaded_pip = _tryDownloadOrderedSet()

    try:
        sys.path.insert(0, downloaded_pip)
        OrderedSet = _tryImportOrderedSet()
    finally:
        del sys.path[0]

    if OrderedSet is None:
        from .OrderedSetsFallback import OrderedSet


def buildOrderedSet(*producers):
    """Helper function to merge multiple producers into one OrderedSet value"""
    values = []

    for producer in producers:
        values.extend(producer)

    return OrderedSet(values)
