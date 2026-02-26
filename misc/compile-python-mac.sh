#!/bin/bash
#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

set -e # Exit immediately if a command exits with a non-zero status.

# --- Configuration ---
# Set the Python version you want to build.
# Using a specific, stable patch release is recommended.
PY_VER="3.11.9"

# Set the desired installation path.
INSTALL_PREFIX="/opt/python-for-nuitka-${PY_VER}"

PY_MAJOR_MINOR=$(echo "$PY_VER" | cut -d. -f1-2) # e.g., 3.11
TARBALL="Python-$PY_VER.tar.xz"
SOURCE_DIR="Python-$PY_VER"

BUILD_CONFIG="Release"
BUILD_TARGET="Build"
EXTRA_CONFIGURE_OPTS="--enable-optimizations --with-lto"

while [[ "$#" -gt 0 ]]; do
    case $1 in
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
        *)
            echo "Unknown parameter passed: $1"
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

if [[ "$(uname)" == "Darwin" ]]; then
    # --- macOS Dependencies ---
    echo "Installing macOS dependencies via Homebrew..."
    eval $(/opt/homebrew/bin/brew shellenv)
    brew install pkg-config openssl@3 xz gdbm tcl-tk mpdecimal zstd ccache

    # Set flags for macOS to find Homebrew-installed libraries
    export LDFLAGS="-L$(brew --prefix openssl@3)/lib -L$(brew --prefix xz)/lib -L$(brew --prefix gdbm)/lib"
    export CPPFLAGS="-I$(brew --prefix openssl@3)/include -I$(brew --prefix xz)/include -I$(brew --prefix gdbm)/include"
    # Point configure to the correct openssl
    export CONFIGURE_OPTS="--with-openssl=$(brew --prefix openssl@3)"
    export MAKE_JOBS=$(sysctl -n hw.ncpu)

    export PYTHON_BINARY=./$SOURCE_DIR/python.exe

    export MACOSX_DEPLOYMENT_TARGET=10.9
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
        # Use wget. -O specifies the output file.
        wget -O "$TARBALL" "$URL"

    # If wget is not found, check if curl is available
    elif command -v curl >/dev/null 2>&1; then
        echo "wget not found. Using curl to download..."
        # Use curl. -o specifies the output file, -L follows redirects.
        curl -L -o "$TARBALL" "$URL"

    # If neither is found, exit with an error
    else
        echo "Error: Neither wget nor curl is available on this system." >&2
        echo "Please install one of them to proceed." >&2
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

    # --prefix:         Install location
    # --disable-shared: CRITICAL. This prevents building libpython.so/dylib
    #                   and builds only libpythonX.Y.a
    ./configure \
        --prefix="$INSTALL_PREFIX" \
        --disable-shared \
        $EXTRA_CONFIGURE_OPTS \
        $CONFIGURE_OPTS
else
    echo "Makefile exists, skipping configure for incremental build..."
fi

# --- 4. Build and Install ---
echo "Building Python... This will take a long time due to PGO."
make -j$MAKE_JOBS
cd -

$PYTHON_BINARY -m ensurepip
$PYTHON_BINARY -m pip install -r /dev/stdin <<EOF
# Onefile compression
zstandard >= 0.15; python_version >= '3.5'

# Wheels
wheel
EOF

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
