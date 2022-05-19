%if 0%{?rhel} < 8
# detect python site-packages path, use get_python_lib(0) as nuitka using
%if 0%{?fedora} < 31
%global python_sitearch %(%{__python} -c "import sys, distutils.sysconfig; sys.stdout.write(distutils.sysconfig.get_python_lib(0))")
%endif
%global python3_sitearch %(%{__python3} -c "import sys, distutils.sysconfig; sys.stdout.write(distutils.sysconfig.get_python_lib(0))")
%endif

%global _python_bytecompile_errors_terminate_build 0

Name:           nuitka
Version:        VERSION
Release:        5%{?dist}
Summary:        Python compiler with full language support and CPython compatibility
Group:          Development/Languages/Python
License:        Apache-2.0
URL:            https://nuitka.net/
Source0:        https://nuitka.net/releases/Nuitka-%{version}.tar.gz
Source1:        nuitka-rpmlintrc
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
%if 0%{?fedora} < 28 && 0%{?rhel} < 8
BuildRequires:  python
BuildRequires:  python-devel
BuildRequires:  python-setuptools
%endif
%if 0%{?fedora} < 31 && 0%{?rhel} < 8
BuildRequires:  python-markupsafe
%endif
%if 0%{?fedora} >= 24
BuildRequires:  python-libs
BuildRequires:  python-debug
%endif
%if 0%{?fedora} >= 24 || 0%{?suse_version} >= 1500
BuildRequires:  python3
BuildRequires:  python3-devel
%endif
%if 0%{?rhel} == 8
BuildRequires:  python36
BuildRequires:  python36-devel
%endif
%if 0%{?fedora} >= 24 || 0%{?rhel} == 8
BuildRequires:  python3-markupsafe
%endif
%if 0%{?suse_version} >= 1500
BuildRequires:  python3-MarkupSafe
%endif
%if 0%{?fedora} >= 27
BuildRequires:  python3-tools
%endif
%if 0%{?fedora} >= 35 || 0%{?suse_version} >= 1500
BuildRequires:  python3-setuptools
%endif
BuildRequires:  gcc-c++
BuildRequires:  strace
BuildRequires:  patchelf
BuildRequires:  ccache
BuildRequires:  gdb

%if 0%{?fedora} < 28 && 0%{?rhel} < 8
Requires:       python-devel
%endif
%if 0%{?fedora} >= 24 || 0%{?suse_version} >= 1500
Requires:       python3-devel
%endif
%if 0%{?rhel} == 8
Requires:       python36-devel
%endif
%if 0%{?fedora} < 31 && 0%{?rhel} < 8
Requires:       python-markupsafe
%endif
%if 0%{?fedora} >= 24 || 0%{?rhel} == 8
Requires:       python3-markupsafe
%endif
%if 0%{?suse_version} >= 1500
Requires:       python3-MarkupSafe
%endif
Requires:       gcc-c++
Requires:       strace
Requires:       patchelf
Requires:       ccache

BuildArchitectures: noarch

%description
Python compiler with full language support and CPython compatibility

This Python compiler achieves full language compatibility and compiles Python
code into compiled objects that are not second class at all. Instead they can
be used in the same way as pure Python objects.

%prep
%setup -q -n Nuitka-%{version}

%build

python2=`which python2 2>/dev/null || true`
if [ "$python2" != "" ]
then
    python2_version=`$python2 -c "import sys; print '.'.join(str(s) for s in sys.version_info[0:2])"`
fi
python3=`which python3 2>/dev/null || true`

# Only used on Windows:
rm -rf nuitka/build/inline_copy/lib/scons-4*

if [ "$python2_version" != "2.6" ]
then
    # Remove files needed only for Python 2.6, they only cause errors during
    # compilation with Python3.
    rm -rf nuitka/build/inline_copy/lib/scons-2.3.2
else
    # Remove files mot needed for Python 2.6, they only cause errors during
    # compilation with Python 2.6.
    rm -rf nuitka/build/inline_copy/lib/scons-3.1.2
    rm -rf nuitka/build/inline_copy/tqdm
fi

# These are all Windows only or used only there.
rm -rf nuitka/build/inline_copy/clcache
rm -rf nuitka/build/inline_copy/atomicwrites
rm -rf nuitka/build/inline_copy/colorama

if [ "$python2" != "" ]
then
    python2_version=`$python2 -c "import sys; print '.'.join(str(s) for s in sys.version_info[0:2])"`
    $python2 setup.py build
fi

if [ "$python3" != "" ]
then
    $python3 setup.py build
fi

%check

echo "Environment variables during build:"
env

echo "OS information during build:"
if [ -f /etc/os-release ]
then
    echo "Contents of /etc/os-release :"
    cat /etc/os-release
else
    echo "No /etc/os-release file found"
fi

if [ -f /etc/SuSE-release ]
then
    echo "Contents of /etc/SuSE-release :"
    cat /etc/SuSE-release
else
    echo "No /etc/SuSE-release file found"
fi

if [ -f /etc/issue ]
then
    echo "Contents of /etc/issue :"
    cat /etc/issue
else
    echo "No /etc/issue file found"
fi


if [ -x "$(command -v lsb_release)" ]
then
    lsb_release -a
else
    echo "No lsb_release binary found"
fi


python2=`which python2 || true`

if [ "$python2" != "" ]
then
    echo "Nuitka Version information"
    $python2 -m nuitka.__main__ --version
    echo "Basic compilation test of empty module:"
    $python2 -m nuitka.__main__ --module --show-scons --run tests/basics/Empty.py
    echo "Basic compilation test of empty program:"
    $python2 -m nuitka.__main__ --show-scons --run tests/basics/Empty.py

    $python2 ./tests/run-tests --skip-reflection-test
else
    echo "Nuitka Version information"
    python3 -m nuitka --version
    echo "Basic compilation test of empty module:"
    python3 -m nuitka --module --show-scons --run tests/basics/Empty.py
    echo "Basic compilation test of empty program:"
    python3 -m nuitka --show-scons --run tests/basics/Empty.py

    python3 ./tests/run-tests --skip-reflection-test
fi

%install
rm -rf %{buildroot}

python2=`which python2 || true`
python3=`which python3 || true`

if [ "$python2" != "" ]
then
    $python2 setup.py install --skip-build --prefix %{_prefix} --root=%{buildroot}
fi

if [ "$python3" != "" ]
then
    $python3 setup.py install --skip-build --prefix %{_prefix} --root=%{buildroot}
fi

mkdir -p %{buildroot}%{_mandir}/man1
gzip -c doc/nuitka2.1 > %{buildroot}%{_mandir}/man1/nuitka2.1.gz
cp %{buildroot}%{_mandir}/man1/nuitka2.1.gz %{buildroot}%{_mandir}/man1/nuitka3.1.gz
gzip -c doc/nuitka2-run.1 > %{buildroot}%{_mandir}/man1/nuitka2-run.1.gz
cp %{buildroot}%{_mandir}/man1/nuitka2-run.1.gz %{buildroot}%{_mandir}/man1/nuitka3-run.1.gz

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%doc README.rst Changelog.rst
%if 0%{?fedora} < 31 && 0%{?rhel} < 8
%{_bindir}/nuitka2
%{_bindir}/nuitka2-run
%{python_sitearch}/*
%endif
%{_mandir}/man1/*
%if 0%{?fedora} >= 24 || 0%{?suse_version} >= 1500
%{python3_sitearch}/*
%{_bindir}/nuitka3
%{_bindir}/nuitka3-run
%endif
%if 0%{?rhel} == 8
/usr/lib/python3.6/site-packages/
%{_bindir}/nuitka3
%{_bindir}/nuitka3-run
%endif
%changelog
* Sat Dec 28 2019 Kay Hayen<kay.hayen@gmail.com> - 0.6.7
- adapted for Fedora31 and CentOS 8, Python3 enhancements
- added Python3 for openSUSE 15 or higher too.

* Fri Jun 07 2019 Kay Hayen<kay.hayen@gmail.com> - 0.6.4
- adapted for Fedora30

* Mon Mar 26 2018 Kay Hayen<kay.hayen@gmail.com> - 0.5.29
- added Python3 packaging

* Sun Sep 08 2013 Kay Hayen <kay.hayen@gmail.com> - 0.4.6
- changed description to match what we use for Debian

* Fri Mar 15 2013 Kay Hayen <kay.hayen@gmail.com> - 0.4.2
- addressed complaints from opensuse buildservice
- moved to group "/Development/Languages/Python"
- no trailing dot for description,
- man pages also for Python3 related binaries

* Sun Mar 10 2013 ownssh <ownssh@gmail.com> - 0.4.1-3
- use shortcut files to support python3 (remove python3 base package)
- change requires python to python-devel

* Thu Mar 07 2013 ownssh <ownssh@gmail.com> - 0.4.1-2
- Add python3 support

* Thu Mar 07 2013 ownssh <ownssh@gmail.com> - 0.4.1-1
- Initial packaging of Nuitka as RPM.
