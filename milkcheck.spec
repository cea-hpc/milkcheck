%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%define vimdatadir %{_datadir}/vim/vimfiles


Name:		milkcheck
Version:	1.0
Release:	1%{?dist}
Summary:	Distributed cluster command management

Group:		System Environment/Base
License:	CeCILL
Source0:	%{name}-%{version}.tar.gz
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildArch:	noarch
BuildRequires:	python-devel python-setuptools asciidoc
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
make install DESTDIR=%{buildroot} PYTHON=%{__python} MANDIR=%{_mandir} \
             SYSCONFIGDIR=%{_sysconfdir} VIMDATADIR=%{vimdatadir}

%clean
rm -rf $RPM_BUILD_ROOT


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
* Sat May 25 2013 Aurelien Degremont <aurelien.degremont@cea.fr> 1.0-1
- Update to 1.0 release (UI fixes).

* Thu Mar 18 2013 Aurelien Degremont <aurelien.degremont@cea.fr> 0.11.1-1
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
