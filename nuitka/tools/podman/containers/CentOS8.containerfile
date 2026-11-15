#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

ARG CENTOS_VERSION
FROM centos:stream8
ENV container docker
USER root

RUN rm -f /etc/yum.repos.d/CentOS-Stream-*.repo \
    && printf '%s\n' \
        '[baseos]' \
        'name=CentOS Stream 8 - BaseOS' \
        'baseurl=https://vault.centos.org/8-stream/BaseOS/$basearch/os/' \
        'gpgcheck=1' \
        'enabled=1' \
        'gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial' \
        '' \
        '[appstream]' \
        'name=CentOS Stream 8 - AppStream' \
        'baseurl=https://vault.centos.org/8-stream/AppStream/$basearch/os/' \
        'gpgcheck=1' \
        'enabled=1' \
        'gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial' \
        '' \
        '[extras]' \
        'name=CentOS Stream 8 - Extras' \
        'baseurl=https://vault.centos.org/8-stream/extras/$basearch/os/' \
        'gpgcheck=1' \
        'enabled=1' \
        'gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial' \
        '' \
        '[powertools]' \
        'name=CentOS Stream 8 - PowerTools' \
        'baseurl=https://vault.centos.org/8-stream/PowerTools/$basearch/os/' \
        'gpgcheck=1' \
        'enabled=1' \
        'gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial' \
        > /etc/yum.repos.d/centos-stream.repo

RUN dnf install -y epel-release scl-utils gcc-toolset-13 \
    && dnf repolist \
    && dnf install -y \
        ccache \
        gcc \
        gdb \
        make \
        patchelf \
        python3-devel \
        python3-zstandard \
        strace \
        wget \
    && echo 'source /opt/rh/gcc-toolset-13/enable' >> /root/.bashrc \
    && echo 'source /opt/rh/gcc-toolset-13/enable' >> /root/.bash_profile \
    && dnf clean -y all

VOLUME [ "/sys/fs/cgroup" ]
CMD ["/usr/sbin/init"]

#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
