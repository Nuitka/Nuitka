#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""For Linux desktop file and AppStream metainfo creation"""

import os
import sys
import time
from xml.sax.saxutils import escape

from nuitka.options.Options import (
    getCompanyName,
    getFileDescription,
    getFileVersion,
    getLinuxAppConsoleMode,
    getLinuxAppLicense,
    getLinuxIconPaths,
    getProductName,
    getProductVersion,
)
from nuitka.OutputDirectories import (
    getResultFullpath,
    getStandaloneDirectoryPath,
)
from nuitka.PythonVersions import python_version_str
from nuitka.utils.FileOperations import (
    copyFile,
    getFilenameExtension,
    openTextFile,
)


def _getLinuxIconPath():
    icon_paths = getLinuxIconPaths()

    if icon_paths:
        return icon_paths[0]

    # Default to Python icon if available.
    # spell-checker: ignore pixmaps
    default_icons = (
        "/usr/share/pixmaps/python%s.xpm" % python_version_str,
        "/usr/share/pixmaps/python%s.xpm" % sys.version_info[0],
        "/usr/share/pixmaps/python.xpm",
    )

    for icon in default_icons:
        if os.path.exists(icon):
            return icon

    return None


def _getLinuxIconInfo(app_id):
    """Icon source path, filename and icon name to use for the app.

    Notes:
        The icon file is named after the application id, as recommended
        by the freedesktop icon theme specification, to avoid collisions
        in the icon theme directories.
    """
    icon_path = _getLinuxIconPath()

    if icon_path is not None:
        icon_filename = app_id + getFilenameExtension(icon_path)

        return icon_path, icon_filename, app_id

    return None, None, None


def _makeLinuxAppIdSegment(value):
    allowed_chars = "abcdefghijklmnopqrstuvwxyz0123456789"

    result = "".join((char if char in allowed_chars else "_") for char in value.lower())

    while "__" in result:
        result = result.replace("__", "_")

    result = result.strip("_")

    if not result or result[0].isdigit():
        result = "_" + result

    return result


def _getLinuxAppId():
    """AppStream component id derived from company and product names."""
    return "com.%s.%s" % (
        _makeLinuxAppIdSegment(getCompanyName()),
        _makeLinuxAppIdSegment(getProductName()),
    )


def _escapeXmlAttributeValue(value):
    return escape(value, {'"': "&quot;"})


def _getReleaseDate():
    source_date_epoch = os.environ.get("SOURCE_DATE_EPOCH")

    if source_date_epoch is not None and source_date_epoch.isdigit():
        return time.strftime("%Y-%m-%d", time.gmtime(int(source_date_epoch)))

    return time.strftime("%Y-%m-%d")


def _createLinuxMetainfoFile(logger, target_dir, app_id, binary_name, icon_name):
    company_name = getCompanyName()
    product_name = getProductName()
    file_description = getFileDescription()

    project_license = getLinuxAppLicense()
    if project_license == "Proprietary":
        project_license = "LicenseRef-proprietary"

    metainfo_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<component type="desktop-application">',
        "  <id>%s</id>" % escape(app_id),
        "  <metadata_license>FSFAP</metadata_license>",
        "  <project_license>%s</project_license>" % escape(project_license),
        "  <name>%s</name>" % escape(product_name),
    ]

    if file_description is not None:
        metainfo_lines.append("  <summary>%s</summary>" % escape(file_description))
        metainfo_lines.append("  <description>")
        metainfo_lines.append("    <p>%s</p>" % escape(file_description))
        metainfo_lines.append("  </description>")

    developer_id = app_id.rsplit(".", 1)[0]

    metainfo_lines.append(
        '  <developer id="%s">' % _escapeXmlAttributeValue(developer_id)
    )
    metainfo_lines.append("    <name>%s</name>" % escape(company_name))
    metainfo_lines.append("  </developer>")

    if icon_name is not None:
        metainfo_lines.append('  <icon type="stock">%s</icon>' % escape(icon_name))

    metainfo_lines.append(
        '  <launchable type="desktop-id">%s.desktop</launchable>' % escape(app_id)
    )

    metainfo_lines.append("  <provides>")
    metainfo_lines.append("    <binary>%s</binary>" % escape(binary_name))
    metainfo_lines.append("  </provides>")

    release_version = getProductVersion() or getFileVersion()

    if release_version is not None:
        metainfo_lines.append("  <releases>")
        metainfo_lines.append(
            '    <release version="%s" date="%s"/>'
            % (_escapeXmlAttributeValue(release_version), _getReleaseDate())
        )
        metainfo_lines.append("  </releases>")

    metainfo_lines.append("</component>")

    metainfo_filename = os.path.join(target_dir, app_id + ".metainfo.xml")

    with openTextFile(
        filename=metainfo_filename, mode="w", encoding="utf8"
    ) as metainfo_file:
        metainfo_file.write("\n".join(metainfo_lines) + "\n")

    logger.info("Created AppStream metainfo file '%s'." % metainfo_filename)


def createLinuxAppFiles(logger, onefile):
    """Create the Linux desktop file and AppStream metainfo file.

    Notes:
        For onefile, these are created alongside the onefile binary,
        otherwise they are created inside the dist folder.
    """
    result_filename = getResultFullpath(onefile=onefile, real=True)

    if onefile:
        target_dir = os.path.dirname(result_filename)
    else:
        target_dir = getStandaloneDirectoryPath(bundle=False, real=False)

    binary_name = os.path.basename(result_filename)

    app_id = _getLinuxAppId()
    product_name = getProductName()
    file_description = getFileDescription()

    icon_path, icon_filename, icon_name = _getLinuxIconInfo(app_id=app_id)

    if icon_path is not None:
        copyFile(icon_path, os.path.join(target_dir, icon_filename))

    desktop_lines = [
        "[Desktop Entry]",
        "Type=Application",
        "Version=1.5",
        "Name=%s" % product_name,
    ]

    if file_description is not None:
        desktop_lines.append("Comment=%s" % file_description)

    desktop_lines.append("TryExec=%s" % binary_name)
    desktop_lines.append("Exec=%s" % binary_name)

    if icon_name is not None:
        desktop_lines.append("Icon=%s" % icon_name)

    if getLinuxAppConsoleMode() == "force":
        desktop_lines.append("Terminal=true")
    else:
        desktop_lines.append("Terminal=false")

    desktop_lines.append("Categories=Utility;")

    desktop_filename = os.path.join(target_dir, app_id + ".desktop")

    with openTextFile(
        filename=desktop_filename, mode="w", encoding="utf8"
    ) as desktop_file:
        desktop_file.write("\n".join(desktop_lines) + "\n")

    logger.info("Created desktop file '%s'." % desktop_filename)

    _createLinuxMetainfoFile(
        logger=logger,
        target_dir=target_dir,
        app_id=app_id,
        binary_name=binary_name,
        icon_name=icon_name,
    )


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
