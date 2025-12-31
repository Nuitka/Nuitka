#!/usr/bin/env python3
#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Script to generate Visual Studio Code configuration file.

This detects the Python include path and version, and the MSVC compiler path and
Windows SDK version. It then generates a "c_cpp_properties.json" file that can be
used by Visual Studio Code on the given system.
"""

import os
import sys

# Add Nuitka's inline copy of Jinja2 to sys.path
# Assuming this script is in 'misc/' and 'nuitka/' is in the root
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo_root)

# isort:start

import sysconfig

from nuitka.utils.FileOperations import getFileContents, putTextFileContents
from nuitka.utils.Jinja2 import getTemplateFromString


def getPythonInfo():
    """Detects Python include path and version."""
    include_path = sysconfig.get_path("include")
    version_hex = hex((sys.version_info.major << 8) | (sys.version_info.minor << 4))

    return include_path, version_hex


def getMSVCInfo():
    """Detects MSVC compiler path and Windows SDK version."""
    # This is a simplified version of what Nuitka does,
    # leveraging the existing Utils if possible, or re-implementing if needed.
    # Nuitka's getMSVCRedistPath finds the redist folder, but we need the compiler.

    # Let's try to use vswhere directly as Nuitka does in Utils.py
    # but we need to find the compiler, not just the redist.
    # spell-checker: ignore vswhere

    # Return driven and many cases to deal with,
    # pylint: disable=too-many-branches,too-many-locals,too-many-return-statements
    vswhere_path = None

    for candidate in ("ProgramFiles(x86)", "ProgramFiles"):
        program_files_dir = os.getenv(candidate)
        if program_files_dir:
            candidate_path = os.path.join(
                program_files_dir,
                "Microsoft Visual Studio",
                "Installer",
                "vswhere.exe",
            )
            if os.path.exists(candidate_path):
                vswhere_path = candidate_path
                break

    if not vswhere_path:
        print("Error: vswhere.exe not found.")
        return None, None

    import subprocess

    # Find latest VS installation
    try:
        output = (
            subprocess.check_output(
                [
                    vswhere_path,
                    "-latest",
                    "-products",
                    "*",
                    "-requires",
                    "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                    "-property",
                    "installationPath",
                ]
            )
            .decode()
            .strip()
        )
    except subprocess.CalledProcessError:
        print("Error: Failed to run vswhere.exe")
        return None, None

    if not output:
        print("Error: No suitable Visual Studio installation found.")
        return None, None

    vs_path = output

    # Find MSVC compiler
    vc_tools_version_file = os.path.join(
        vs_path, "VC", "Auxiliary", "Build", "Microsoft.VCToolsVersion.default.txt"
    )
    if os.path.exists(vc_tools_version_file):
        vc_version = getFileContents(vc_tools_version_file).strip()
    else:
        # Fallback: list directories in VC/Tools/MSVC and take the latest
        msvc_base = os.path.join(vs_path, "VC", "Tools", "MSVC")
        if os.path.exists(msvc_base):
            versions = sorted(os.listdir(msvc_base))
            if versions:
                vc_version = versions[-1]
            else:
                print("Error: No MSVC versions found.")
                return None, None
        else:
            print("Error: MSVC directory not found.")
            return None, None

    # Determine architecture, spell-checker: ignore Hostx64, Hostx86
    arch = "x64" if sys.maxsize > 2**32 else "x86"
    host_arch = (
        "Hostx64" if os.getenv("PROCESSOR_ARCHITECTURE") == "AMD64" else "Hostx86"
    )

    compiler_path = os.path.join(
        vs_path, "VC", "Tools", "MSVC", vc_version, "bin", host_arch, arch, "cl.exe"
    )

    if not os.path.exists(compiler_path):
        print(f"Error: Compiler not found at {compiler_path}")
        return None, None

    # Detect Windows SDK Version
    # This is a bit tricky without opening a developer command prompt.
    # We can look into the registry or check standard paths.
    # A common way is to look at the include paths in the registry or
    # check 'C:\Program Files (x86)\Windows Kits\10\Include'

    sdk_version = "10.0.19041.0"  # Default fallback

    kits_root = os.path.join(
        os.getenv("ProgramFiles(x86)", "C:\\Program Files (x86)"),
        "Windows Kits",
        "10",
        "Include",
    )
    if os.path.exists(kits_root):
        versions = [d for d in os.listdir(kits_root) if d.startswith("10.")]
        if versions:
            # Sort by version
            versions.sort(key=lambda s: [int(u) for u in s.split(".")])
            sdk_version = versions[-1]

    return compiler_path, sdk_version


def getPluginIncludePaths(repo_root):
    """Scans for plugin directories containing C/C++ header files."""
    plugin_includes = []
    base_plugins_dir = os.path.join(repo_root, "nuitka", "plugins")

    if not os.path.exists(base_plugins_dir):
        return []

    for root, _, files in os.walk(base_plugins_dir):
        # We only care if the directory contains header files directly
        if any(f.endswith(".h") or f.endswith(".hpp") for f in files):
            rel_path = os.path.relpath(root, repo_root)
            # Ensure forward slashes for VSCode config
            path_str = "${workspaceFolder}/" + rel_path.replace("\\", "/")
            plugin_includes.append(path_str)

    return sorted(plugin_includes)


def getCompilerInfo():
    """Detects compiler path and IntelliSense mode based on OS."""
    if sys.platform == "win32":
        compiler_path, sdk_version = getMSVCInfo()
        return compiler_path, sdk_version, "msvc-x64"
    else:
        # Linux and macOS detection
        compiler_path = "/usr/bin/gcc"
        if not os.path.exists(compiler_path):
            compiler_path = "/usr/bin/clang"

        if sys.platform == "darwin":
            mode = "macos-clang-x64"  # Default to clang on macOS
            if not os.path.exists(compiler_path) and os.path.exists("/usr/bin/clang"):
                compiler_path = "/usr/bin/clang"
        else:
            mode = "linux-gcc-x64"

        return compiler_path, "", mode


def main():
    print("Generating .vscode/c_cpp_properties.json...")

    python_include, python_version = getPythonInfo()
    print(f"Python Include: {python_include}")
    print(f"Python Version: {python_version}")

    compiler_path, sdk_version, intelliSenseMode = getCompilerInfo()

    if not compiler_path:
        print("Failed to detect compiler.")
        return 1

    print(f"Compiler Path: {compiler_path}")
    if sdk_version:
        print(f"Windows SDK Version: {sdk_version}")
    print(f"IntelliSense Mode: {intelliSenseMode}")

    plugin_include_paths = getPluginIncludePaths(repo_root)
    print(f"Found {len(plugin_include_paths)} plugins with headers.")

    template_path = os.path.join(repo_root, ".vscode", "c_cpp_properties.json.j2")
    template_str = getFileContents(template_path)

    # Render template
    # We use Nuitka's Jinja2 wrapper

    output = getTemplateFromString(template_str).render(
        python_include_path=python_include,
        python_version_hex=python_version,
        compiler_path=compiler_path,
        windows_sdk_version=sdk_version,
        intelliSenseMode=intelliSenseMode,
        plugin_include_paths=plugin_include_paths,
    )

    output_path = os.path.join(repo_root, ".vscode", "c_cpp_properties.json")
    putTextFileContents(output_path, output)

    print(f"Successfully generated {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

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
