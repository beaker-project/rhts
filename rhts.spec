%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?pyver: %global pyver %(%{__python} -c "import sys ; print sys.version[:3]")}

Name: rhts
Summary: Automated software testing
Version: 4.12
Release: 1%{?dist}
Group: Development/Libraries
License: GPL
Source0: http://fedorahosted.org/releases/r/h/%{name}-%{version}.tar.gz
Buildroot: %{_tmppath}/%{name}-%{version}-root
BuildArch: noarch
BuildRequires: python-devel
%if 0%{?rhel}%{?fedora} > 4
BuildRequires: selinux-policy-devel
%endif

%description
This package is intended for people creating and maintaining tests, and
contains (or requires) the runtime components of the test system for 
installation on a workstation, along with development tools.

%package devel
Summary: Testing
Group: Development/Libraries
Obsoletes: rhts-rh-devel
Provides: rhts-rh-devel
Requires: rhts-test-env = %{version}

%description devel
This package contains components of the test system used when running 
tests, either on a developer's workstation, or within a lab.

%package test-env
Summary: Testing API
Group: Development/Libraries
Obsoletes: rhts-testhelpers
Provides: rhts-testhelpers
Obsoletes: rhts-test-env-lab
Provides: rhts-test-env-lab
Obsoletes: rhts-devel-test-env
Provides: rhts-devel-test-env
Obsoletes: rhts-legacy
Provides: rhts-legacy
Requires: beakerlib
%if 0%{?rhel}%{?fedora} > 4
Requires(post): policycoreutils
%endif

%description test-env
This package contains components of the test system used when running 
tests, either on a developer's workstation, or within a lab.

%prep
%setup -q


%build
[ "$RPM_BUILD_ROOT" != "/" ] && [ -d $RPM_BUILD_ROOT ] && rm -rf $RPM_BUILD_ROOT;
pushd python-modules
CFLAGS="$RPM_OPT_FLAGS" %{__python} setup.py build
popd

%install
DESTDIR=$RPM_BUILD_ROOT make install
pushd python-modules 
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT
popd

%if 0%{?rhel}%{?fedora} > 4
# Build RHTS Selinux Testing Policy 
pushd selinux
make -f %{_datadir}/selinux/devel/Makefile
install -p -m 644 -D rhts.pp $RPM_BUILD_ROOT%{_datadir}/selinux/packages/%{name}/rhts.pp
popd
%endif

# Legacy support.
ln -s rhts-db-submit-result $RPM_BUILD_ROOT/usr/bin/rhts_db_submit_result
ln -s rhts-environment.sh $RPM_BUILD_ROOT/usr/bin/rhts_environment.sh
ln -s rhts-sync-set $RPM_BUILD_ROOT/usr/bin/rhts_sync_set
ln -s rhts-sync-block $RPM_BUILD_ROOT/usr/bin/rhts_sync_block
ln -s rhts-submit-log $RPM_BUILD_ROOT/usr/bin/rhts_submit_log
mkdir -p $RPM_BUILD_ROOT/mnt/scratchspace
mkdir -p $RPM_BUILD_ROOT/mnt/testarea

%clean
[ "$RPM_BUILD_ROOT" != "/" ] && [ -d $RPM_BUILD_ROOT ] && rm -rf $RPM_BUILD_ROOT;

%post test-env
%if 0%{?rhel}%{?fedora} > 4
if [ "$1" -le "1" ] ; then # First install
semodule -i %{_datadir}/selinux/packages/%{name}/rhts.pp 2>/dev/null || :
fi
%endif

%preun test-env
%if 0%{?rhel}%{?fedora} > 4
if [ "$1" -lt "1" ] ; then # Final removal
semodule -r rhts 2>/dev/null || :
fi
%endif

%postun test-env
%if 0%{?rhel}%{?fedora} > 4
if [ "$1" -ge "1" ] ; then # Upgrade
semodule -i %{_datadir}/selinux/packages/%{name}/rhts.pp 2>/dev/null || :
fi
%endif

%files test-env
%defattr(-,root,root)
%attr(0755, root, root)%{_bindir}/rhts-db-submit-result
%attr(0755, root, root)%{_bindir}/rhts_db_submit_result
%attr(0755, root, root)%{_bindir}/rhts-environment.sh
%attr(0755, root, root)%{_bindir}/rhts_environment.sh
%attr(0755, root, root)%{_bindir}/rhts-run-simple-test
%attr(0755, root, root)%{_bindir}/rhts-report-result
%attr(0755, root, root)%{_bindir}/rhts-submit-log
%attr(0755, root, root)%{_bindir}/rhts_submit_log
%attr(0755, root, root)%{_bindir}/rhts-sync-block
%attr(0755, root, root)%{_bindir}/rhts_sync_block
%attr(0755, root, root)%{_bindir}/rhts-sync-set
%attr(0755, root, root)%{_bindir}/rhts_sync_set
%attr(0755, root, root)%{_bindir}/rhts-recipe-sync-block
%attr(0755, root, root)%{_bindir}/rhts-recipe-sync-set
%attr(0755, root, root)%{_bindir}/rhts-reboot
%attr(0755, root, root)%{_bindir}/rhts-backup
%attr(0755, root, root)%{_bindir}/rhts-restore
%attr(0755, root, root)%{_bindir}/rhts-system-info
%attr(0755, root, root)%{_bindir}/rhts-abort
%attr(0755, root, root)%{_bindir}/rhts-test-runner.sh
%attr(0755, root, root)%{_bindir}/rhts-test-checkin
%attr(0755, root, root)%{_bindir}/rhts-test-update
%{_datadir}/%{name}/lib/rhts-make.include
%{_datadir}/%{name}/failurestrings
%{_datadir}/%{name}/falsestrings
%if 0%{?rhel}%{?fedora} > 4
%{_datadir}/selinux/packages/%{name}/rhts.pp
%endif
%{python_sitelib}/%{name}*
/mnt/scratchspace
%attr(1777,root,root)/mnt/testarea

%files devel
%defattr(-,root,root)
%attr(0755, root, root)%{_bindir}/rhts-create-new-test
%attr(0755, root, root)%{_bindir}/rhts-wizard
%attr(0755, root, root)%{_bindir}/rhts-lint
%attr(0755, root, root)%{_bindir}/rhts-run-package
%attr(0755, root, root)%{_libexecdir}/rhts/rhts-mk-build-package
%attr(0755, root, root)%{_libexecdir}/rhts/rhts-mk-snake-template
%attr(0755, root, root)%{_libexecdir}/rhts/rhts-mk-generate-specfile
%attr(0755, root, root)%{_libexecdir}/rhts/rhts-mk-get-current-tag
%attr(0755, root, root)%{_libexecdir}/rhts/rhts-mk-get-next-tag
%attr(0755, root, root)%{_libexecdir}/rhts/rhts-mk-get-test-package-name
%attr(0755, root, root)%{_libexecdir}/rhts/rhts-mk-get-version-info
%attr(0755, root, root)%{_libexecdir}/rhts/rhts-mk-tag-release
%attr(0755, root, root)%{_libexecdir}/rhts/rhts-mk-test-import
%attr(0755, root, root)%{_libexecdir}/rhts/rhts-mk-diff-since-last-tag
%doc doc/Makefile.template
%doc doc/runtest.sh.template

%changelog
* Wed Jun 09 2010 Bill Peck <bpeck@redhat.com> 4.12-1
- tell ausearch to only look at the logs, ignore stdin (bpeck@redhat.com)
- add missing rhts_workflow (bpeck@redhat.com)

* Fri Jun 04 2010 Bill Peck <bpeck@redhat.com> 4.10-1
- add missing rhts namespace (bpeck@redhat.com)

* Thu Jun 03 2010 Bill Peck <bpeck@redhat.com> 4.9-1
- New rhts
