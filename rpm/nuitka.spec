# detect python site-packages path, use get_python_lib(0) as nuitka using
%global python_sitearch %(%{__python} -c "import sys, distutils.sysconfig; sys.stdout.write(distutils.sysconfig.get_python_lib(0))")

%global python3_sitearch %(%{__python3} -c "import sys, distutils.sysconfig; sys.stdout.write(distutils.sysconfig.get_python_lib(0))")

%global _python_bytecompile_errors_terminate_build 0

Name:           nuitka
Version:        VERSION
Release:        5%{?dist}
Summary:        Python compiler with full language support and CPython compatibility
Group:          Development/Languages/Python
License:        Apache License 2.0
URL:            http://nuitka.net/
Source0:        http://nuitka.net/releases/Nuitka-%{version}.tar.gz
Source1:        nuitka-rpmlintrc
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires:  python
BuildRequires:  python-devel
BuildRequires:  python-setuptools
%if 0%{?fedora} >= 22
BuildRequires: python3-devel
BuildRequires: python-tools
%endif
%if 0%{?fedora} >= 24
BuildRequires: python-libs
BuildRequires: python-debug
%endif
%if 0%{?fedora} >= 27
BuildRequires: python3-tools
%endif
BuildRequires:  gcc-c++
BuildRequires:  strace
BuildRequires:  chrpath
Requires:       python-devel
Requires:       gcc-c++
Requires:       strace
BuildArchitectures: noarch

%description
Python compiler with full language support and CPython compatibility

This Python compiler achieves full language compatibility and compiles Python
code into compiled objects that are not second class at all. Instead they can be
used in the same way as pure Python objects.

%prep
%setup -q -n Nuitka-%{version}

%build
%{__python} setup.py build
%if 0%{?fedora} >= 27
%{__python} setup.py build
%endif

%check
./tests/run-tests --skip-reflection-test

%install
rm -rf %{buildroot}
%{__python} setup.py install --skip-build --prefix %{_prefix} --root=%{buildroot}
%if 0%{?fedora} >= 27
%{__python3} setup.py install --skip-build --prefix %{_prefix} --root=%{buildroot}
%endif
mkdir -p %{buildroot}%{_mandir}/man1
gzip -c doc/nuitka.1 > %{buildroot}%{_mandir}/man1/nuitka.1.gz
cp %{buildroot}%{_mandir}/man1/nuitka.1.gz %{buildroot}%{_mandir}/man1/nuitka3.1.gz
gzip -c doc/nuitka-run.1 > %{buildroot}%{_mandir}/man1/nuitka-run.1.gz
cp %{buildroot}%{_mandir}/man1/nuitka-run.1.gz %{buildroot}%{_mandir}/man1/nuitka3-run.1.gz

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%doc README.rst Changelog.rst
%{_bindir}/nuitka
%{_bindir}/nuitka-run
%{_mandir}/man1/*
%{python_sitearch}/*
%if 0%{?fedora} >= 27
%{python3_sitearch}/*
%{_bindir}/nuitka3
%{_bindir}/nuitka3-run
%endif

%changelog
* Sun Sep 08 2013 Kay Hayen <kay.hayen@gmail.com 0.4.6
- changed description to match what we use for Debian

* Fri Mar 15 2013 Kay Hayen <kay.hayen@gmail.com 0.4.2
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
- Initial package
