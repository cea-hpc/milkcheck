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
%{__python} setup.py build

%install
rm -rf %{buildroot}
%{__python} setup.py install -O1 --skip-build --root %{buildroot}

# config files
install -d %{buildroot}/%{_sysconfdir}/%{name}/conf/samples
install -p -m 0644 conf/samples/*.yaml %{buildroot}/%{_sysconfdir}/%{name}/conf/samples

%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%config %{_sysconfdir}/%{name}
%{python_sitelib}/MilkCheck/
%{python_sitelib}/MilkCheck-*-py?.?.egg-info
%{_bindir}/milkcheck

%changelog
* Mon Jul 25 2011  Aurelien Degremont <aurelien.degremont@cea.fr> 0.6-1
- Initial package
