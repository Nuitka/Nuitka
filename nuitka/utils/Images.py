#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .FileOperations import getFilenameExtension, hasFilenameExtension
from .Utils import isMacOS, isWin32Windows


def checkIconUsage(logger, icon_path):
    icon_format = getFilenameExtension(icon_path)

    if icon_format != ".icns" and isMacOS():
        needs_conversion = True
    elif icon_format != ".ico" and isWin32Windows():
        needs_conversion = True
    else:
        needs_conversion = False

    if needs_conversion:
        try:
            import imageio  # pylint: disable=I0021,import-error,unused-import
        except ImportError:
            logger.sysexit(
                """\
Need to install 'imageio' to let automatically convert the non native \
icon image (%s) in file in '%s'."""
                % (icon_format[1:].upper(), icon_path)
            )


def convertImageToIconFormat(logger, image_filename, converted_icon_filename):
    """Convert image file to icon file."""
    icon_format = converted_icon_filename.rsplit(".", 1)[1].lower()

    # Limit to supported icon formats.
    assert hasFilenameExtension(converted_icon_filename, (".ico", ".icns")), icon_format

    # Avoid importing unless actually used.
    import imageio  # pylint: disable=I0021,import-error

    try:
        image = imageio.imread(image_filename)
    except ValueError:
        logger.sysexit(
            "Unsupported file format for 'imageio' in '%s', use e.g. PNG or other supported file formats instead."
            % image_filename
        )

    imageio.imwrite(converted_icon_filename, image)
