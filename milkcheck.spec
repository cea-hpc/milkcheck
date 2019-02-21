%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%define vimdatadir %{_datadir}/vim/vimfiles


Name:          milkcheck
Version:       1.2.1
Release:       1%{?dist}
Summary:       Distributed cluster command management

Group:         System Environment/Base
License:       CeCILL
Source0:       https://github.com/cea-hpc/milkcheck/archive/v%{version}.tar.gz#/%{name}-%{version}.tar.gz
BuildArch:     noarch
BuildRequires: python-devel
BuildRequires: python-setuptools
BuildRequires: asciidoc
Requires:      clustershell >= 1.7

%description
Manage a cluster-wide system through configuration based commands. It offers a
easy to use interface to manage services, with dependencies and various
actions, all of them based on shell commands.

%prep
%setup -q

%build
make

%install
make install DESTDIR="%{buildroot}" PYTHON=%{__python} MANDIR=%{_mandir} \
             SYSCONFIGDIR=%{_sysconfdir} VIMDATADIR=%{vimdatadir}

%files
%defattr(-,root,root,-)
%config %{_sysconfdir}/%{name}/conf
%config(noreplace) %{_sysconfdir}/%{name}/milkcheck.conf
%{python_sitelib}/MilkCheck/
%{python_sitelib}/MilkCheck-*-py?.?.egg-info
%{_bindir}/milkcheck
%{_mandir}/man8/*
%doc AUTHORS
%doc README.md
%doc ChangeLog
%doc Licence_CeCILL_V2-en.txt
%doc Licence_CeCILL_V2-fr.txt
%{vimdatadir}/ftdetect/milkcheck.vim
%{vimdatadir}/syntax/milkcheck.vim

%changelog
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
