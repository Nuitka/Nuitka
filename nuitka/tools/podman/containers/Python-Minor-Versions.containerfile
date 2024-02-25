#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

FROM debian:buster

# Install dependencies
RUN apt-get update && apt-get install -y curl wget build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev gdb

# Install Python 3.7.3
RUN wget https://www.python.org/ftp/python/3.7.3/Python-3.7.3.tgz \
 && tar -xf Python-3.7.3.tgz \
 && cd Python-3.7.3 \
 && ./configure --prefix=/opt/python3.7.3/ --disable-shared --enable-ipv6 --enable-optimizations LDFLAGS='-Xlinker -export-dynamic -rdynamic' \
 && make LDFLAGS='-Xlinker -export-dynamic -rdynamic' \
 && make install

# Install Python 3.7.4
RUN wget https://www.python.org/ftp/python/3.7.4/Python-3.7.4.tgz \
 && tar -xf Python-3.7.4.tgz \
 && cd Python-3.7.4 \
 && ./configure --prefix=/opt/python3.7.4/ --disable-shared --enable-ipv6 --enable-optimizations LDFLAGS='-Xlinker -export-dynamic -rdynamic' \
 && make LDFLAGS='-Xlinker -export-dynamic -rdynamic' \
 && make install

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
