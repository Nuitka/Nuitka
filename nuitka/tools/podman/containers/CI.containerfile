#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

FROM debian:12-slim
ENV container docker
ENV NUITKA_PIP_FLAGS="--break-system-packages"

VOLUME [ "/sys/fs/cgroup" ]

## Install what we use for CI generally
RUN mkdir /src
RUN apt-get update && apt-get install -y \
    apt-utils \
    ccache \
    chrpath \
    devscripts \
    dh-python \
    dput \
    gcc \
    gdb \
    git \
    help2man \
    libzstd-dev \
    lintian \
    patchelf \
    python3 \
    python3-all-dbg \
    python3-all-dev \
    python3-appdirs \
    python3-dev \
    python3-glob2 \
    python3-pip \
    python3-stdeb \
    rst2pdf \
    rsync \
    scons \
    strace \
    sudo \
    wget


## Clean up APT when done.
RUN apt-get clean && rm -rf "/var/lib/apt/lists/*" "/tmp/*" "/var/tmp/*"

## Do what git asks us to do, for working with git checkouts.
RUN git config --global --add safe.directory /src

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
