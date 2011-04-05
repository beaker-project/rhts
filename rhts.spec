%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?pyver: %global pyver %(%{__python} -c "import sys ; print sys.version[:3]")}

Name: rhts
Summary: Automated software testing
Version: 4.32
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
Requires: beaker-client

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
%attr(0755, root, root)%{_bindir}/rhts-extend
%{_datadir}/%{name}/lib/rhts-make.include
%{_datadir}/%{name}/failurestrings
%{_datadir}/%{name}/falsestrings
%if 0%{?rhel}%{?fedora} > 4
%{_datadir}/selinux/packages/%{name}/rhts.pp
%endif
%{python_sitelib}/%{name}*
/mnt/scratchspace
%attr(1777,root,root)/mnt/testarea
%doc doc/README

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
* Tue Apr 05 2011 Marian Csontos <mcsontos@redhat.com> 4.32-1
- bz644805 - Added hook to run scripts on watchdog (mcsontos@redhat.com)
- bz688218 - make rpm does not handle regexp metachars in test names
  (bpeck@redhat.com)

* Fri Mar 11 2011 Bill Peck <bpeck@redhat.com> 4.31-1
- Support uefibootmgr on all arches that have it installed. (bpeck@redhat.com)
- sanity checks for git tags (dcallagh@redhat.com)
- rhts-run-simple-test doesn't need to use tee -a, produces redundant output.
  (bpeck@redhat.com)
- rhts-mk-get-current-tag ignores packed-refs (dcallagh@redhat.com)

* Mon Feb 07 2011 Bill Peck <bpeck@redhat.com> 4.30-1
- ignore rpm -q error. (bpeck@redhat.com)
- Avoid reporting selinux errors on the harness itself. (bpeck@redhat.com)
- bz664764 - rhts-devel and svn+ssh problem (mcsontos@redhat.com)

* Fri Jan 14 2011 Bill Peck <bpeck@redhat.com> 4.29-1
- revert tighter selinux controls (bpeck@redhat.com)
- Added: CompatService to RhtsOptions (mcsontos@redhat.com)

* Fri Dec 17 2010 Bill Peck <bpeck@redhat.com> 4.28-1
- use /mnt/testarea instead of /tmp.  /tmp should not be used as it will
  trigger avc errors. (bpeck@redhat.com)
- make package not working with local git repos (mcsontos@redhat.com)

* Mon Dec 06 2010 Bill Peck <bpeck@redhat.com> 4.27-1
- Merge branch 'master' of ssh://git.fedorahosted.org/git/rhts
  (bpeck@redhat.com)
- extend watchdog's directly through lab controller. (bpeck@redhat.com)

* Tue Nov 30 2010 Marian Csontos <mcsontos@redhat.com> 4.26-1
- Added: Print selinux status into AVCs (mcsontos@redhat.com)
- Fixed: ausearch always using en_US date format (mcsontos@redhat.com)

* Wed Nov 24 2010 Marian Csontos <mcsontos@redhat.com> 4.25-1
- Enhanced ausearch (mcsontos@redhat.com)

* Thu Nov 18 2010 Bill Peck <bpeck@redhat.com> 4.24-1
- make it work with python2.7 (bpeck@redhat.com)

* Mon Nov 08 2010 Bill Peck <bpeck@redhat.com> 4.23-1
- bz640395  -  make bkradd does not work (bpeck@redhat.com)
- Added: Environment and RhtsOptions to metadata (mcsontos@redhat.com)

* Wed Sep 08 2010 Bill Peck <bpeck@redhat.com> 4.22-1
- Merge branch 'TESTOUT' (mcsontos@redhat.com)
- Make prev. TESTOUT patch prettier (mcsontos@redhat.com)
- fix rhts-db-submit-result mkstemp on rhel3. (bpeck@redhat.com)
- Fixed re-sending TESTOUT.log (mcsontos@redhat.com)

* Wed Sep 01 2010 Marian Csontos <mcsontos@redhat.com> 4.21-1
- Fixed wrong timestamp format
- Improved AVC logging.

* Fri Aug 27 2010 Marian Csontos <mcsontos@redhat.com> 4.20-1
- PartialRevert "BZ616455 - Report all AVC denials" (mcsontos@redhat.com)

* Tue Aug 24 2010 Marian Csontos <mcsontos@redhat.com> 4.19-1
- Use runuser instead of su (mcsontos@redhat.com)

* Mon Aug 16 2010 Marian Csontos <mcsontos@redhat.com> 4.18-1
- BZ616455 - Report all AVC denials (ebenes@redhat.com)

* Tue Jul 13 2010 Bill Peck <bpeck@redhat.com> 4.17-1
- Update to require beaker-client (bpeck@redhat.com)

* Tue Jun 29 2010 Bill Peck <bpeck@redhat.com> 4.16-1
- fix rhts-test-runner.sh logic. (bpeck@redhat.com)

* Thu Jun 17 2010 Bill Peck <bpeck@redhat.com> 4.15-1
- Include Marians patch for md5/sha/none.  Allows FIPS testing to work.
  (bpeck@redhat.com)
- bz605360 prevent rhts-mk-get-current-tag from confusing (bpeck@redhat.com)

* Fri Jun 11 2010 Bill Peck <bpeck@redhat.com> 4.14-1
- sync up with 108 (bpeck@redhat.com)

* Wed Jun 09 2010 Bill Peck <bpeck@redhat.com> 4.13-1
- tell ausearch to only look at the logs, ignore stdin (bpeck@redhat.com)
- add missing rhts_workflow (bpeck@redhat.com)

* Fri Jun 04 2010 Bill Peck <bpeck@redhat.com> 4.10-1
- add missing rhts namespace (bpeck@redhat.com)

* Thu Jun 03 2010 Bill Peck <bpeck@redhat.com> 4.9-1
- New rhts
