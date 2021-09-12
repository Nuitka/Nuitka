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
""" Handling of images, esp. format conversions for icons.

"""

from .FileOperations import hasFilenameExtension


def convertImageToIconFormat(logger, image_filename, icon_filename):
    """Convert image file to icon file."""
    icon_format = icon_filename.rsplit(".", 1)[1].lower()

    # Limit to supported icon formats.
    assert hasFilenameExtension(icon_filename, (".ico", ".icns")), icon_format

    try:
        import imageio
    except ImportError:
        logger.sysexit(
            "Need to install 'imageio' to automatically convert non-%s icon image file in '%s'."
            % (icon_format, image_filename)
        )

    try:
        image = imageio.imread(image_filename)
    except ValueError:
        logger.sysexit(
            "Unsupported file format for imageio in '%s', use e.g. PNG files."
            % image_filename
        )

    imageio.imwrite(icon_filename, image)
