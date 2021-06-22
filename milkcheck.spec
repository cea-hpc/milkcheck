%{!?__python_name: %global __python_name python3}
%{!?__python_sitelib: %global __python_sitelib %(%{__python_name} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

%global vimdatadir %{_datadir}/vim/vimfiles

Name:          milkcheck
Version:       1.2.4
Release:       1%{?dist}
Summary:       Distributed cluster command management

Group:         System Environment/Base
License:       CeCILL
Source0:       https://github.com/cea-hpc/milkcheck/archive/v%{version}.tar.gz#/%{name}-%{version}.tar.gz
BuildArch:     noarch
Requires:      %{__python_name}-%{name} = %{version}

%global _description %{expand:
Manage a cluster-wide system through configuration based commands. It offers a
easy to use interface to manage services, with dependencies and various
actions, all of them based on shell commands.}

%description %{_description}

%package -n %{__python_name}-%{name}
Summary:       Distributed cluster command management
BuildRequires: %{__python_name}-devel
BuildRequires: %{__python_name}-setuptools
BuildRequires: asciidoc
Requires:      clustershell >= 1.7


%description -n %{__python_name}-%{name} %{_description}

%prep
%setup -q

%build
make PYTHON=%{__python_name}

%install
make install DESTDIR="%{buildroot}" PYTHON=%{__python_name} MANDIR=%{_mandir} \
             SYSCONFIGDIR=%{_sysconfdir} VIMDATADIR=%{vimdatadir}

%files
%defattr(-,root,root,-)
%config %{_sysconfdir}/%{name}/conf
%config(noreplace) %{_sysconfdir}/%{name}/milkcheck.conf
%{_bindir}/milkcheck
%{_mandir}/man8/*
%doc AUTHORS
%doc README.md
%doc ChangeLog
%doc Licence_CeCILL_V2-en.txt
%doc Licence_CeCILL_V2-fr.txt
%{vimdatadir}/ftdetect/milkcheck.vim
%{vimdatadir}/syntax/milkcheck.vim

%files -n %{__python_name}-%{name}
%{__python_sitelib}/MilkCheck/
%{__python_sitelib}/MilkCheck-*-py?.?.egg-info
%doc AUTHORS
%doc README.md
%doc ChangeLog
%doc Licence_CeCILL_V2-en.txt
%doc Licence_CeCILL_V2-fr.txt

%changelog
* Tue Jun 22 2021 Aurelien Cedeyn <aurelien.cedeyn@cea.fr> 1.2.4-1
- Update to 1.2.4 release (fix pkg_resources version).

* Tue Feb 02 2021 Aurelien Cedeyn <aurelien.cedeyn@cea.fr> 1.2.3-1
- Update to 1.2.3 release (python3 support).

* Thu Feb 21 2019 Aurelien Cedeyn <aurelien.cedeyn@cea.fr> 1.2.2-1
- Update to 1.2.2 release.

* Thu Feb 21 2019 Aurelien Cedeyn <aurelien.cedeyn@cea.fr> 1.2.1-1
- Update to 1.2.1 release.

* Fri Oct 05 2018 Aurelien Degremont <aurelien.degremont@cea.fr> - 1.2-1
- Update to 1.2 release

* Wed Oct 11 2017 Aurelien Degremont <aurelien.degremont@cea.fr> 1.1-1
- Update to 1.1 release.

* Sat May 25 2013 Aurelien Degremont <aurelien.degremont@cea.fr> 1.0-1
- Update to 1.0 release (UI fixes).

* Mon Mar 18 2013 Aurelien Degremont <aurelien.degremont@cea.fr> 0.11.1-1
- milkcheck.conf is declared as 'noreplace'.
- Update to 0.11.1 release. (--nodeps, engine bugfixes, ...)

* Thu Feb 21 2013 Aurelien Degremont <aurelien.degremont@cea.fr> 0.11-1
- Update to 0.11 release. (--define, custom reverse action, ...)

* Thu Feb  7 2013 Aurelien Degremont <aurelien.degremont@cea.fr> 0.10-1
- Update to 0.10 release. (--quiet, new syntax, interactive mode, ...)

* Fri Nov  9 2012 Aurelien Degremont <aurelien.degremont@cea.fr> 0.9.2-1
- Update to 0.9.2 release. (Bugfixes, man page, --dry-run mode, ...)

* Wed Oct 24 2012 Aurelien Cedeyn <aurelien.cedeyn@cea.fr> 0.8.1
- Manage build process inside Makefile

* Mon Jul 25 2011  Aurelien Degremont <aurelien.degremont@cea.fr> 0.6-1
- Initial package
