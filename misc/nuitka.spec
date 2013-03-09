# detect python site-packages path, use get_python_lib(0) as nuitka using
%global python_sitearch %(%{__python} -c "import sys, distutils.sysconfig; sys.stdout.write(distutils.sysconfig.get_python_lib(0))")

# enable python3 support when python3 package available
%global with_python3 %(rpm -qi python3 &> /dev/null && echo 1 || echo 0)

# enable python3 support for recent fedora
%if 0%{?fedora} && 0%{?fedora} >= 18
%global with_python3 1
%endif

# detect python site-packages path
%if 0%{?with_python3}
%global python3_sitearch %(%{__python3} -c "import sys, distutils.sysconfig; sys.stdout.write(distutils.sysconfig.get_python_lib(0))")
%endif # with_python3

Name:		nuitka
Version:		0.4.1
Release:		2%{?dist}
Summary:		A Python compiler translates the Python into a C++ program.
Group:		Development/Languages
License:		Apache License 2.0
URL:			http://nuitka.net/
Source0:		http://nuitka.net/releases/Nuitka-%{version}.tar.gz
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:  python
BuildRequires:  python-devel
BuildRequires:  gcc-c++
Requires: python
Requires: gcc-c++

%description
Nuitka is a good replacement for the Python interpreter and compiles
every construct that CPython 2.6, 2.7 and 3.2 offer.

It translates the Python into a C++ program that then uses "libpython"
to execute in the same way as CPython does, in a very compatible way.

It is somewhat faster than CPython already, but currently it doesn't
make all the optimizations possible, but a 258% factor on pystone is
a good start (number is from version 0.3.11).

%if 0%{?with_python3}
%package -n python3-nuitka
Summary:		A Python compiler translates the Python into a C++ program for Python3.
Group:		Development/Languages
BuildRequires: python3
BuildRequires: python3-devel
Requires: python3

%description -n python3-nuitka
Nuitka is a good replacement for the Python interpreter and compiles
every construct that CPython 2.6, 2.7 and 3.2 offer.

It translates the Python into a C++ program that then uses "libpython"
to execute in the same way as CPython does, in a very compatible way.

It is somewhat faster than CPython already, but currently it doesn't
make all the optimizations possible, but a 258% factor on pystone is
a good start (number is from version 0.3.11).

%endif # with_python3

%prep
%setup -q -n Nuitka-%{version}
%patch0 -p1 -b .python3-setup
%patch1 -p1 -b .python3-exec

%if 0%{?with_python3}
rm -rf %{py3dir}
cp -a . %{py3dir}
%endif # with_python3

%build
%{__python} setup.py build

%if 0%{?with_python3}
pushd %{py3dir}
%{__python3} setup.py build
popd
%endif # with_python3

%install
rm -rf %{buildroot}

%if 0%{?with_python3}
pushd %{py3dir}
%{__python3} setup.py install --skip-build --root=%{buildroot}
popd
mv %{buildroot}%{_bindir}/nuitka %{buildroot}%{_bindir}/python3-nuitka
mv %{buildroot}%{_bindir}/nuitka-python %{buildroot}%{_bindir}/python3-nuitka-python
%endif # with_python3

%{__python} setup.py install --skip-build --root=%{buildroot}

mkdir -p %{buildroot}%{_mandir}/man1
gzip -c doc/nuitka.1 > %{buildroot}%{_mandir}/man1/nuitka.1.gz
gzip -c doc/nuitka-python.1 > %{buildroot}%{_mandir}/man1/nuitka-python.1.gz

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%doc README.txt Changelog.rst
%{_bindir}/nuitka
%{_bindir}/nuitka-python
%{_mandir}/man1/*
%{python_sitearch}/*

%if 0%{?with_python3}
%files -n python3-nuitka
%defattr(-,root,root,-)
%{_bindir}/python3-nuitka
%{_bindir}/python3-nuitka-python
%{python3_sitearch}/*
%endif # with_python3

%changelog
* Thu Mar 07 2013 ownssh <ownssh@gmail.com> - 0.4.1-2
- Add python3 support

* Thu Mar 07 2013 ownssh <ownssh@gmail.com> - 0.4.1-1
- Initial package
