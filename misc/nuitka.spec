# detect python site-packages path, use get_python_lib(0) as nuitka using
%global python_sitearch %(%{__python} -c "import sys, distutils.sysconfig; sys.stdout.write(distutils.sysconfig.get_python_lib(0))")

Name:           nuitka
Version:        0.4.3pre5
Release:        5%{?dist}
Summary:        A Python compiler translates the Python into a C++ program
Group:          Development/Languages/Python
License:        Apache License 2.0
URL:            http://nuitka.net/
Source0:        http://nuitka.net/releases/Nuitka-%{version}.tar.gz
Source1:        nuitka-python3
Source2:        nuitka-rpmlintrc
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires:  python
BuildRequires:  python-devel
BuildRequires:  gcc-c++
Requires:       python-devel
Requires:       gcc-c++
BuildArchitectures: noarch

%description
Nuitka is a good replacement for the Python interpreter and compiles
every construct that CPython 2.6, 2.7 and 3.2 offer.

It translates the Python into a C++ program that then uses "libpython"
to execute in the same way as CPython does, in a very compatible way.

It is somewhat faster than CPython already, but currently it doesn't
make all the optimizations possible, but a 258% factor on pystone is
a good start (number is from version 0.3.11).

%prep
%setup -q -n Nuitka-%{version}

%build
%{__python} setup.py build

%check
./misc/check-release

%install
rm -rf %{buildroot}
%{__python} setup.py install --skip-build --prefix %{_prefix} --root=%{buildroot}
install -D -m755 %{SOURCE1} %{buildroot}%{_bindir}/nuitka3
install -D -m755 %{SOURCE1} %{buildroot}%{_bindir}/nuitka-python3
mkdir -p %{buildroot}%{_mandir}/man1
gzip -c doc/nuitka.1 > %{buildroot}%{_mandir}/man1/nuitka.1.gz
cp %{buildroot}%{_mandir}/man1/nuitka.1.gz %{buildroot}%{_mandir}/man1/nuitka3.1.gz
gzip -c doc/nuitka-python.1 > %{buildroot}%{_mandir}/man1/nuitka-python.1.gz
cp %{buildroot}%{_mandir}/man1/nuitka-python.1.gz %{buildroot}%{_mandir}/man1/nuitka-python3.1.gz

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%doc README.txt Changelog.rst
%{_bindir}/nuitka
%{_bindir}/nuitka-python
%{_bindir}/nuitka3
%{_bindir}/nuitka-python3
%{_mandir}/man1/*
%{python_sitearch}/*

%changelog
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
