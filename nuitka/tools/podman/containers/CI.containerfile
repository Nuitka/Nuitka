#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

FROM debian:12-slim
ENV container docker

VOLUME [ "/sys/fs/cgroup" ]

## Install what we use for CI generally
RUN mkdir /src
RUN apt-get update && apt-get install -y \
    apt-utils \
    ccache \
    chrpath \
    dput \
    gcc \
    gdb \
    git \
    help2man \
    lintian \
    python3 \
    python3-dev \
    python3-pip \
    rst2pdf \
    strace \
    wget


## Clean up APT when done.
RUN apt-get clean && rm -rf "/var/lib/apt/lists/*" "/tmp/*" "/var/tmp/*"

## Do what git asks us to do, for working with git checkouts.
RUN git config --global --add safe.directory /src

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
