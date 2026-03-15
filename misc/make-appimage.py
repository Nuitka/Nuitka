#!/usr/bin/env python3
#     Copyright 2026, Simon Robin Lehn, MIT license, see end of file
#
# Build a self-contained Nuitka AppImage for Linux.
#
# Requirements on the build host:
#   - python3, python3-dev, python3-venv
#   - patchelf, ccache
#   - mksquashfs (squashfs-tools)
#   - gcc
#   - Internet access (downloads appimagetool runtime)
#
# The resulting AppImage bundles Python, dev headers, patchelf, ccache,
# and all Nuitka dependencies. Only a C compiler ($CC) is needed on the
# target system.
#
# Usage:
#   python3 misc/make-appimage.py [--python /path/to/python3]

import argparse
import base64
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(*args, **kwargs):
    """Run a command, raising on failure."""
    kwargs.setdefault("check", True)
    return subprocess.run(*args, **kwargs)


def capture(*args, **kwargs):
    """Run a command and return stripped stdout."""
    kwargs.setdefault("check", True)
    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("text", True)
    return subprocess.run(*args, **kwargs).stdout.strip()


def python_query(python, code):
    """Run a Python one-liner and return the output."""
    return capture([python, "-c", code])


def get_ldd_deps(binary):
    """Return non-glibc shared library paths needed by a binary."""
    skip = {"libc.so", "libm.so", "libdl.so", "librt.so", "libpthread.so",
            "ld-linux", "linux-vdso"}
    deps = []
    try:
        output = capture(["ldd", binary])
    except subprocess.CalledProcessError:
        return deps
    for line in output.splitlines():
        if "=> /" not in line:
            continue
        lib_path = line.split("=> ")[1].split(" (")[0].strip()
        lib_name = os.path.basename(lib_path)
        if any(lib_name.startswith(s) for s in skip):
            continue
        deps.append(lib_path)
    return deps


def bundle_binary_with_deps(binary_path, appdir):
    """Copy a binary and its non-glibc shared lib deps into the AppDir."""
    bin_name = os.path.basename(binary_path)
    shutil.copy2(binary_path, appdir / "usr" / "bin" / bin_name)
    lib_dir = appdir / "usr" / "lib"
    for dep in get_ldd_deps(binary_path):
        dep_name = os.path.basename(dep)
        if not (lib_dir / dep_name).exists():
            shutil.copy2(dep, lib_dir / dep_name)


def fix_absolute_symlinks(directory, resolve=False):
    """Fix or remove absolute symlinks in a directory (non-recursive).

    If resolve is True, replace absolute symlinks pointing to existing files
    with copies. Remove dangling absolute symlinks either way.
    """
    for entry in directory.iterdir():
        if not entry.is_symlink():
            continue
        target = os.readlink(entry)
        if not target.startswith("/"):
            continue
        if resolve and os.path.isfile(target):
            entry.unlink()
            shutil.copy2(target, entry)
        else:
            entry.unlink()


def fix_libpython_symlinks(lib_dir, pyver):
    """Make libpython symlinks relative and ensure the linker .so exists."""
    for f in lib_dir.glob(f"libpython{pyver}*.so"):
        if not f.is_symlink():
            continue
        target = os.readlink(f)
        if target.startswith("/"):
            f.unlink()
            f.symlink_to(os.path.basename(target))
    versioned = lib_dir / f"libpython{pyver}.so.1.0"
    linker = lib_dir / f"libpython{pyver}.so"
    if versioned.exists() and not linker.exists():
        linker.symlink_to(versioned.name)


def write_apprun(appdir):
    """Write the AppRun entry point."""
    apprun = appdir / "AppRun"
    apprun.write_text("""\
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "$0")")"
export PATH="${HERE}/usr/bin:${PATH}"
export PYTHONHOME="${HERE}/usr"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"

# Prefer system patchelf/ccache if installed and version >= bundled.
_ver() { "$1" --version 2>&1 | head -1 | grep -oE "[0-9]+\\.[0-9]+(\\.[0-9]+)?" | head -1; }
_prefer_tool() {
    local bundled="$1" envvar="$2"
    [ -x "$bundled" ] || return
    local tool_name sys_path
    tool_name="$(basename -- "$bundled")"
    sys_path="$(PATH="/usr/local/bin:/usr/bin:/bin" command -v "$tool_name" 2>/dev/null)" || {
        export "$envvar=$bundled"; return
    }
    local sv bv
    sv="$(_ver "$sys_path")"
    bv="$(_ver "$bundled")"
    if [ -n "$sv" ] && [ -n "$bv" ] && \\
       [ "$(printf '%s\\n%s\\n' "$bv" "$sv" | sort -V | tail -1)" = "$sv" ]; then
        export "$envvar=$sys_path"
    else
        export "$envvar=$bundled"
    fi
}
_prefer_tool "${HERE}/usr/bin/patchelf" NUITKA_PATCHELF_BINARY
_prefer_tool "${HERE}/usr/bin/ccache"   NUITKA_CCACHE_BINARY

exec "${HERE}/usr/bin/python3" -m nuitka "$@"
""")
    apprun.chmod(0o755)


def write_desktop(appdir):
    """Write the .desktop file."""
    (appdir / "nuitka.desktop").write_text("""\
[Desktop Entry]
Type=Application
Name=Nuitka
Exec=nuitka
Icon=nuitka
Categories=Development;
Terminal=true
Comment=Python Compiler
X-AppImage-Integrate=false
""")


def write_icon(appdir):
    """Write a minimal 1x1 PNG icon."""
    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
        "2mNkYPj/HwADBwIAMCbHYQAAAABJRU5ErkJggg=="
    )
    (appdir / "nuitka.png").write_bytes(png)


def write_sitecustomize(stdlib_dir):
    """Write sitecustomize.py to add site-packages to sys.path.

    Debian Python uses dist-packages but pip in a venv installs to
    site-packages. This ensures both are on sys.path regardless of flavor.
    """
    (stdlib_dir / "sitecustomize.py").write_text("""\
import os
import site
import sys

_appimage_site = os.path.join(sys.prefix, "lib",
    "python" + ".".join(str(x) for x in sys.version_info[:2]),
    "site-packages")
if os.path.isdir(_appimage_site) and _appimage_site not in sys.path:
    site.addsitedir(_appimage_site)
""")


def get_appimagetool(arch):
    """Download appimagetool if not already present, return its path."""
    tool = os.environ.get("APPIMAGETOOL")
    if tool and os.path.isfile(tool):
        return tool
    tool = f"/tmp/appimagetool-{arch}"
    if os.path.isfile(tool) and os.access(tool, os.X_OK):
        return tool
    print("==> Downloading appimagetool...")
    run(["curl", "-fsSL",
         f"https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-{arch}.AppImage",
         "-o", tool])
    os.chmod(tool, 0o755)
    return tool


def find_system_lib(name):
    """Search common library paths for a shared library."""
    machine = platform.machine()
    for prefix in [f"/lib/{machine}-linux-gnu", "/lib64", "/usr/lib"]:
        path = os.path.join(prefix, name)
        if os.path.isfile(path):
            return path
    return None


def main():
    parser = argparse.ArgumentParser(description="Build a Nuitka AppImage")
    parser.add_argument("--python", default=os.environ.get("PYTHON", "python3"))
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    python = args.python
    script_dir = Path(__file__).resolve().parent
    nuitka_src = script_dir.parent
    arch = platform.machine()

    pyver = python_query(python, "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')")
    pyabi = python_query(python, "import sys; print(sys.abiflags if hasattr(sys, 'abiflags') else '')")
    nuitka_version = re.search(
        r"Nuitka V([0-9rc.]+)",
        (nuitka_src / "nuitka" / "Version.py").read_text(),
    )
    nuitka_version = nuitka_version.group(1) if nuitka_version else "unknown"

    tmpdir = Path(tempfile.mkdtemp())
    appdir = tmpdir / "Nuitka.AppDir"
    output = Path(args.output) if args.output else nuitka_src / f"Nuitka-{nuitka_version}-{arch}.AppImage"

    print("=== Building Nuitka AppImage ===")
    print(f"  Python:  {python} ({pyver})")
    print(f"  Nuitka:  {nuitka_version}")
    print(f"  Arch:    {arch}")
    print(f"  Output:  {output}")
    print()

    # --- Check prerequisites ---
    for tool in ["mksquashfs", "patchelf", "ccache"]:
        if not shutil.which(tool):
            sys.exit(f"Error: '{tool}' is required but not found.")

    # --- Create AppDir with Python venv ---
    print("==> Creating AppDir with Python runtime...")
    for d in ["usr/bin", "usr/lib", "usr/include"]:
        (appdir / d).mkdir(parents=True)

    run([python, "-m", "venv", str(appdir / "usr"), "--without-pip"])
    run([str(appdir / "usr" / "bin" / "python3"), "-m", "ensurepip", "--default-pip"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("==> Installing Nuitka and dependencies...")
    pip = str(appdir / "usr" / "bin" / "pip3")
    run([pip, "install", "--quiet", str(nuitka_src)])
    run([pip, "install", "--quiet",
         "appdirs", "tqdm", "zstandard>=0.15", "pyyaml", "Jinja2>=2.10.2", "ordered-set"])

    # Replace venv Python symlink with real binary
    print("==> Bundling Python runtime...")
    venv_python = appdir / "usr" / "bin" / "python3"
    real_python = Path(os.readlink(venv_python)).resolve() if venv_python.is_symlink() else venv_python
    real_bin = appdir / "usr" / "bin" / "python3.real"
    shutil.copy2(real_python, real_bin)
    for name in ["python3", "python"]:
        link = appdir / "usr" / "bin" / name
        link.unlink(missing_ok=True)
        link.symlink_to("python3.real")

    # Remove pyvenv.cfg so the bundled Python acts as a real installation.
    (appdir / "usr" / "pyvenv.cfg").unlink(missing_ok=True)

    # --- Bundle Python stdlib ---
    stdlib_src = Path(python_query(python, "import sysconfig; print(sysconfig.get_path('stdlib'))"))
    stdlib_dst = appdir / "usr" / "lib" / f"python{pyver}"
    # Copy everything from system stdlib over the venv's stdlib
    for item in stdlib_src.iterdir():
        dst = stdlib_dst / item.name
        if item.is_dir() and not item.is_symlink():
            shutil.copytree(item, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dst, follow_symlinks=False)

    # Resolve dangling absolute symlinks (e.g. sitecustomize.py -> /etc/...)
    fix_absolute_symlinks(stdlib_dst, resolve=True)

    # Write sitecustomize.py after stdlib copy to avoid being overwritten.
    write_sitecustomize(stdlib_dst)

    # --- Bundle libpython shared library ---
    libdir = Path(python_query(python, "import sysconfig; print(sysconfig.get_config_var('LIBDIR'))"))
    lib_dst = appdir / "usr" / "lib"
    for f in libdir.glob(f"libpython{pyver}*"):
        dst = lib_dst / f.name
        if f.is_symlink():
            link_target = os.readlink(f)
            dst.symlink_to(link_target)
        else:
            shutil.copy2(f, dst)
    fix_libpython_symlinks(lib_dst, pyver)

    # --- Bundle Python dev headers ---
    print("==> Bundling Python dev headers...")
    sys_include = Path(python_query(python, "import sysconfig; print(sysconfig.get_path('include'))"))
    if sys_include.is_dir():
        inc_dst = appdir / "usr" / "include" / f"python{pyver}{pyabi}"
        shutil.copytree(sys_include, inc_dst, dirs_exist_ok=True)
    else:
        print(f"Warning: Python dev headers not found at {sys_include}", file=sys.stderr)
        print(f"         Install python{pyver}-dev for full functionality.", file=sys.stderr)

    # --- Bundle Python config dir (Makefile, static lib) ---
    cfgdir = Path(python_query(python, "import sysconfig; print(sysconfig.get_config_var('LIBPL'))"))
    cfgname = cfgdir.name
    cfg_dst = appdir / "usr" / "lib" / f"python{pyver}" / cfgname
    cfg_dst.mkdir(parents=True, exist_ok=True)
    for item in cfgdir.iterdir():
        dst = cfg_dst / item.name
        dst.unlink(missing_ok=True)
        shutil.copy2(item, dst, follow_symlinks=False)
    # Fix config dir .so symlink
    cfg_so = cfg_dst / f"libpython{pyver}.so"
    cfg_so.unlink(missing_ok=True)
    cfg_so.symlink_to(f"../../libpython{pyver}.so.1.0")

    # --- Bundle external tools and their shared lib dependencies ---
    print("==> Bundling patchelf, ccache, and shared library dependencies...")
    patchelf = shutil.which("patchelf")
    if patchelf:
        bundle_binary_with_deps(patchelf, appdir)
    ccache = shutil.which("ccache")
    if ccache:
        bundle_binary_with_deps(ccache, appdir)

    # Also bundle libz and libexpat for Python.
    for lib_name in ["libz.so.1", "libexpat.so.1"]:
        if (lib_dst / lib_name).exists():
            continue
        src = find_system_lib(lib_name)
        if src:
            shutil.copy2(src, lib_dst / lib_name)

    # --- Trim bloat ---
    print("==> Trimming unnecessary files...")
    for pattern in ["**/__pycache__", f"python{pyver}/test",
                     f"python{pyver}/unittest/test", f"python{pyver}/idlelib",
                     f"python{pyver}/tkinter", f"python{pyver}/turtledemo",
                     f"python{pyver}/site-packages/pip*"]:
        for p in (appdir / "usr" / "lib").glob(pattern):
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()

    # --- Create AppRun, desktop file, icon ---
    write_apprun(appdir)
    write_desktop(appdir)
    write_icon(appdir)

    # --- Get appimagetool and build ---
    appimagetool = get_appimagetool(arch)

    print("==> Building AppImage...", flush=True)
    appdir_size = capture(["du", "-sh", str(appdir)]).split()[0]
    print(f"    AppDir size: {appdir_size}", flush=True)

    env = os.environ.copy()
    env["ARCH"] = arch
    run([appimagetool, "--no-appstream", "--comp", "zstd", str(appdir), str(output)], env=env)

    print()
    print("=== Done ===")
    size = output.stat().st_size / (1024 * 1024)
    print(f"{output}  ({size:.1f} MB)")
    print()
    print(f"Test with: {output} --version")

    # Cleanup
    shutil.rmtree(tmpdir)


if __name__ == "__main__":
    main()


# MIT License
#
# Copyright (c) 2026 Simon Robin Lehn
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
