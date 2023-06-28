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

FROM debian:11-slim
ENV container docker

VOLUME [ "/sys/fs/cgroup" ]

# Install what we use for CI generally
COPY requirements-devel.txt /etc/requirements-devel.txt
RUN mkdir /src
RUN apt-get update && apt-get install -y apt-utils gcc python2 python2-dev python3 python3-dev python3-pip git rst2pdf help2man chrpath dput lintian gdb strace ccache

# Install pbuilder extra stuff along with Nuitka build dependencies.
RUN apt-get install -y pbuilder python3-stdeb lintian devscripts reprepro \
    python3-appdirs scons dh-python python3-all-dev python3-all-dbg rsync \
    python3-yaml python3-glob2 patchelf libzstd-dev

RUN python3 -m pip install -U -r /etc/requirements-devel.txt wheel

# Clean up APT when done.
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Do what git asks us to do, for working with git checkouts.
RUN git config --global --add safe.directory /src