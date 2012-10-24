%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Name:		milkcheck
Version:	%{version}
Release:	1%{?dist}
Summary:	Distributed cluster command management

Group:		System Environment/Base
License:	CEA-DAM
Source0:	%{name}-%{version}.tar.gz
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildArch:	noarch
BuildRequires:	python-devel python-setuptools
Requires:	clustershell > 1.4

%description
Manage a cluster-wide system through configuration based commands. It offers a
easy to use interface to manage services, with dependencies and various
actions, all of them based on shell commands.

%prep
%setup -q

%build
make

%install
rm -rf %{buildroot}
make install DESTDIR=%{buildroot} PYTHON=%{__python} MANDIR=%{_mandir} SYSCONFIGDIR=%{_sysconfdir}

%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%config %{_sysconfdir}/%{name}
%{python_sitelib}/MilkCheck/
%{python_sitelib}/MilkCheck-*-py?.?.egg-info
%{_bindir}/milkcheck
%{_mandir}/man8/*

%changelog
* Wed Oct 24 2012 Aurelien Cedeyn <aurelien.cedeyn@cea.fr> 0.8.1
- Manage build process inside Makefile

* Mon Jul 25 2011  Aurelien Degremont <aurelien.degremont@cea.fr> 0.6-1
- Initial package
