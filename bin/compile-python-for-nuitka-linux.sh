#!/bin/bash
#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

set -e # Exit immediately if a command exits with a non-zero status.

# --- Configuration ---
# Set the Python version you want to build.
# Using a specific, stable patch release is recommended.
PY_VER="3.11.9"

# Default set after arguments if not provided
INSTALL_PREFIX=""

PY_MAJOR_MINOR=$(echo "$PY_VER" | cut -d. -f1-2) # e.g., 3.11
TARBALL="Python-$PY_VER.tar.xz"
SOURCE_DIR="Python-$PY_VER"

BUILD_CONFIG="Release"
BUILD_TARGET="Build"
EXTRA_CONFIGURE_OPTS="--enable-optimizations --with-lto"

CLEANUP=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --*=*) # Convert --key=value to --key value
            KEY="${1%%=*}"
            VALUE="${1#*=}"
            shift 1
            set -- "$KEY" "$VALUE" "$@"
            continue
            ;;
        --debug)
            BUILD_CONFIG="Debug"
            # In debug mode, we disable PGO/LTO and enable pydebug, which includes assertions
            EXTRA_CONFIGURE_OPTS="--with-pydebug --without-lto"
            shift
            ;;
        --rebuild)
            BUILD_TARGET="Rebuild"
            shift
            ;;
        --version|--python-version)
            PY_VER="$2"
            TARBALL="Python-$PY_VER.tar.xz"
            SOURCE_DIR="Python-$PY_VER"
            shift 2
            ;;
        --prefix)
            if [[ "$2" == /* ]]; then
                INSTALL_PREFIX="$2"
            elif [[ "$2" == ~* ]]; then
                INSTALL_PREFIX="${2/#\~/$HOME}"
            else
                INSTALL_PREFIX="$PWD/$2"
            fi
            shift 2
            ;;
        --cleanup)
            CLEANUP=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --help, -h       Show this help message and exit"
            echo "  --version <ver>  Specify the Python version to build (default: 3.11.9)"
            echo "  --prefix <dir>   Installation directory (default: /opt/python<version>)"
            echo "  --debug          Build with pydebug and without PGO/LTO"
            echo "  --rebuild        Clean existing build before compiling"
            echo "  --cleanup        Remove the downloaded archive and source directory after successful build"
            exit 0
            ;;
        *)
            echo "Unknown parameter passed: $1"
            echo "Use --help for usage information."
            exit 1
            ;;
    esac
done

echo "--- Starting static Python $PY_VER build for Nuitka ---"
echo "Configuration: $BUILD_CONFIG"
if [[ "$BUILD_CONFIG" == "Release" ]]; then
    echo "PGO is Enabled."
else
    echo "PGO is Disabled. Assertions are Enabled."
fi

if [[ "$(uname)" == "Linux" ]]; then
    SUDO=""
    if [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1; then
        SUDO="sudo"
    fi

    # --- Linux Dependencies ---
    if command -v apt-get >/dev/null 2>&1; then
        echo "Installing Linux dependencies via apt-get..."
        $SUDO apt-get update && $SUDO apt-get install -y curl wget build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev gdb ccache
    elif command -v yum >/dev/null 2>&1; then
        echo "Installing Linux dependencies via yum..."
        $SUDO yum -y install curl wget gcc gcc-c++ make zlib-devel ncurses-devel gdbm-devel nss-devel openssl-devel readline-devel libffi-devel gdb ccache
    elif command -v dnf >/dev/null 2>&1; then
        echo "Installing Linux dependencies via dnf..."
        $SUDO dnf -y install curl wget gcc gcc-c++ make zlib-devel ncurses-devel gdbm-devel nss-devel openssl-devel readline-devel libffi-devel gdb ccache
    else
        echo "Warning: Could not detect package manager. Please ensure build dependencies are installed."
    fi

    # Set flags for Linux if needed
    export MAKE_JOBS=$(nproc)
    if [ -n "$INSTALL_PREFIX" ]; then
        export PYTHON_BINARY="$INSTALL_PREFIX/bin/python3"
    else
        export PYTHON_BINARY="$PWD/$SOURCE_DIR/python"
    fi
else
    echo "Unsupported OS: $(uname)"
    exit 1
fi

# --- 2. Download and Extract Source ---
if [ ! -f "$TARBALL" ]; then
    echo "Downloading $TARBALL..."
    URL="https://www.python.org/ftp/python/$PY_VER/$TARBALL"

    if command -v wget >/dev/null 2>&1; then
        echo "Using wget to download..."
        wget -q -O "$TARBALL" "$URL"
    elif command -v curl >/dev/null 2>&1; then
        echo "wget not found. Using curl to download..."
        curl -sL -o "$TARBALL" "$URL"
    else
        echo "Error: Neither wget nor curl is available on this system." >&2
        exit 1
    fi
else
    echo "Using existing $TARBALL..."
fi

if [ -d "$SOURCE_DIR" ]; then
    echo "Using existing source directory $SOURCE_DIR..."
else
    echo "Extracting $TARBALL..."
    tar -xf "$TARBALL"
fi

# --- 3. Configure Build ---
cd "$SOURCE_DIR"

if [ "$BUILD_TARGET" == "Rebuild" ] && [ -f "Makefile" ]; then
    echo "Rebuild requested. Cleaning existing build..."
    make clean || true
    rm -f Makefile
fi

if [ ! -f "Makefile" ]; then
    echo "Configuring build with optimizations and static linking..."

    PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)

    if [ "$PY_MAJOR" -gt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -ge 6 ]; }; then
        if [[ "$BUILD_CONFIG" == "Release" ]]; then
            EXTRA_CONFIGURE_OPTS="$EXTRA_CONFIGURE_OPTS --with-assertions"
        fi
    fi

    if [ -n "$INSTALL_PREFIX" ]; then
        CONFIGURE_PREFIX_OPTS="--prefix=$INSTALL_PREFIX"
    else
        CONFIGURE_PREFIX_OPTS=""
    fi

    ./configure \
        $CONFIGURE_PREFIX_OPTS \
        --disable-shared \
        --enable-ipv6 \
        LDFLAGS="-Xlinker -export-dynamic -rdynamic" \
        $EXTRA_CONFIGURE_OPTS
else
    echo "Makefile exists, skipping configure for incremental build..."
fi

# --- 4. Build and Install ---
echo "Building Python... This will take a long time due to PGO."
make -j$MAKE_JOBS LDFLAGS="-Xlinker -export-dynamic -rdynamic"
if [ -n "$INSTALL_PREFIX" ]; then
    if [ -w "$INSTALL_PREFIX" ] || [ -w "$(dirname "$INSTALL_PREFIX")" ]; then
        make install
    else
        $SUDO make install
    fi
fi

cd ..

echo "--- Installing ensurepip and requirements ---"
$PYTHON_BINARY -m ensurepip || echo "Warning: ensurepip failed"
$PYTHON_BINARY -m pip install -r /dev/stdin <<EOF
# Onefile compression
zstandard >= 0.15; python_version >= '3.5' and python_version < '3.14'

# Wheels
wheel
EOF

if [ "$CLEANUP" = true ]; then
    echo "--- Cleaning up ---"
    rm -rf "$SOURCE_DIR" "$TARBALL"
fi

echo "--- Build Complete ---"

#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
