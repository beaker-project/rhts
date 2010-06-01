#!/usr/bin/python

import sys, os
from optparse import OptionParser


class RHTSOptions(OptionParser):
	VALIDWORKFLOWS = [ 'beehive_package', 'compare_workflow',
'kernel_workflow', 'milestone_matrix', 'release_package', 'rsync',
'tier1_workflow', 'xen_workflow', 'bringup', 'libworkflow',
'multi-stable-workflow', 'reserve_workflow', 'single_package', 
'tier2_workflow', 'build_package', 'errata_workflow', 'multi_workflow', 
'single_test', 'client_server', 'hardware_vendor', 'matrix_workflow', 
'rawhide_workflow', 'test_lab_machine', 'virt_workflow']
	WORKFLOW = None

	def __init__(self, **kwds):
		""" Constructor. Takes dictionary of values that are valid to
OptionParser constructor. It might also take additional dictionary elements
which will be processed here and then deleted before OptionParser.__init__ is
called with the dictionary that's passed on. Valid additional keys are
"workflow" which will be set to the workflow from which this construction is
called. The workflow passed must be inside the VALIDWORKFLOWS property of the
class. Its sole use is for possible different values to add_option method based
on different workflows"""
		if kwds.has_key('workflow'):
			if kwds['workflow'] not in self.VALIDWORKFLOWS:
				print "Sorry %s is not a known workflow. Valid \
ones are : %s \n If you need to, please add it on %s file." % (kwds['workflow'],
self.VALIDWORKFLOWS, __file__ )
				sys.exit(10)
			self.WORKFLOW = kwds['workflow']
			del kwds['workflow']
		OptionParser.__init__(self, **kwds)
		#print "file is  :%s " % args[0]
		self.loadAllArgs()

	def loadAllArgs(self):
		""" This function gets called from the constructor. Put all
arguments here.. If any of the workflows might be using/doing things
differently, do it here too, based on the WORKFLOW property. 

  The options are listed in lexicographical order, so please keep it that way. 
for consistency reasons, every option that has a short option must have a long
option too. If the option has a short option, short option must be the first
argument, otherwise the long argument must be the first argument"""

		self.add_option("-A", "--add-repo", dest="addrepo", metavar="ADDREPO", 
			action="append",
			help="Location to add repo... i.e. http://hostname/dir;ftp://hostname/dir;file:///full/path/to/dir")
		self.add_option("-a", "--arch", dest="arch", metavar=" ARCH", action="append",
			help="Install this arch on system")
		self.add_option("-C", "--check", dest="check", metavar="CHECK", action="store_true",
			help="Check config by doing all the work except don't schedule.")
		self.add_option("-c", "--container", dest="containers", metavar="CONTAINER", action="append",
			help="set container type to either loopback, partition or lvm")
		self.add_option("-d", "--distro", dest="distro", metavar="DISTRO",
			help="use distribution tree DISTRO")
		self.add_option("-D", "--gdistro", dest="gdistro", metavar="GUESTDISTRO", 
			help="guest's distro. default assumes same as host distro.")
		self.add_option("-e", "--test-repo", dest="test_repo", metavar="REPO",
			help="Include tests from specific repository")
		self.add_option("-E", "--update-errata",  dest="update_errata", metavar="UPDATE_ERRATA",
			action="append", default=[],
			help="Update packages supplied as new in UPDATE_ERRATA")
		self.add_option("-f", "--family", dest="family", metavar="FAMILY",
			help="use distribution family specified")
		self.add_option("-F", "--update-file", dest="update_file", metavar="UPDATE_FILE",
			help="Update to packages listed in UPDATE_FILE")
		self.add_option("-g", "--cpu-flags", dest="cpuflags", metavar=" CPUFLAGS", action="append",
			help="Specify CPU options to be used when choosing test machine")
		self.add_option("--guestparams", dest="guestparams", metavar="GUESTPARAMS", 
			action="append", help="parameters sent to guest_install script. Used to\
 install a domU. Format is same as virt-install params.")
		self.add_option("--guesttest", dest="guesttest", metavar="GUESTTEST", 
			action="store_true", default=False, 
			help="runs all tests INSIDE the first specified guest, as opposed to \
the default behavior of inside the dom0. ")
		self.add_option("--hvm", dest="hvm", metavar="HVM", action="store_true", 
			default=False, help="Require a HVM enabled machine.")
		self.add_option("-i", "--install", dest="pkg_install", metavar="PACKAGE",
			action="append", help="Specify the packages to be installed with this.\
You can use this option multiple times to install multiple packages.")
		self.add_option("-j", "--yum-install", dest="yum_install", metavar="YUMINSTALL", 
			action="append", help="install YUMINSTALL from repository")
		self.add_option("-k", "--koji", dest="koji", metavar="NONR", 
			action="store_true", help="Enable yum repository from koji.fedoraproject.org\
 Used for testing fedora packages. Only works if the OS is  Fedora.")
		self.add_option("-l", "--errata-list", dest="errata_list", action="store_true",
			help="List currently testable errata advisories")
		self.add_option("-m", "--machine", dest="machine", metavar="HOSTNAME",
			help="try to use HOSTNAME for testing")
		self.add_option("-M", "--model", dest="model", metavar=" MODEL",
			help="Specify model name to run tests on")
		self.add_option("-n", "--num-procs", dest="numProcs", metavar=" NUMPROCS",
			action="append", help="Specify the number of processors on test system")
		self.add_option("-N", "--no-run", dest="norun", metavar=" NORUN",
			action="store_true", help="Install requested tests but don't run them")
		self.add_option("-o", "--module", dest="module", metavar="MODULE",
			action="append", help="Specify software module to look for when choosing\
 test machine")
		self.add_option("-p", "--package", dest="package", metavar="PACKAGE",
			action="append", help="include tests for PACKAGE in job ")
		self.add_option("-P", "--allpackages", dest="allpackages", action="store_true",
			help="include all tests for all packages in job")
		self.add_option("-Q", "--quagmire", dest="quagmire", action="store_true",
			help="Use an rt kernel")
		self.add_option("-r", "--released", dest="releasedistro", action="store_true",
			help="Use a released distribution NOTE: Can not be used with -d")
		self.add_option("-R", "--reserve", dest="reserve", metavar="TIME",
			help="Reserve the box after 'gather' step for TIME. Use with responsibility,\
please.")
		self.add_option("-s", "--cpu-speed", dest="cpuspeed", metavar="CPUSPEED",
			action="append", help="Specify the speed (in MHz) of the CPU when choosing\
 test machine")
		self.add_option("-S", "--scheduler", dest="scheduler", metavar="HOSTNAME",
			default="rhts.redhat.com", 
			help="Submit job to scheduler HOSTNAME (default: %default)")
		self.add_option("-t", "--tests", dest="tests", metavar="TEST", action="append",
			default = [], help="Include TESTs in job")
		self.add_option("-T", "--time-limit", dest="timelimit", metavar="TIME",
			help="Set time limit for reservation, qualified by a unit\
 (m, h, d, default: seconds)")
		self.add_option("--tag", dest="tag", action="append",
			help="Run tests on distro matching these tags")
		self.add_option("--tag2", dest="tag2", action="append",
			help="Run tests on distro matching these tags")
		self.add_option("--test-params", dest="testparams", metavar='"name=value"',
			action="append", help="Parameters sent to runtest.sh. \
Can be specified multiple times.  Parameters will be accessible as \
TEST_PARAM_NAME=value")
		self.add_option("--tf", dest="tests_from_file", metavar="TEST(s)",
			action="append", help="Include these TEST(s) in test selection from file \
 Note: Can not be used with -y")
		self.add_option("-u", "--user", dest="submitter", metavar="USER EMAIL",
			help="Set the submitters email")
		self.add_option("-U", "--yum-upgrade", dest="yumupgdpack", metavar="PACKAGE", 
			action="append", help="Yum upgrade package")
		self.add_option("-v", "--variant", dest="variant", metavar="VARIANT",
			help="use variant VARIANT of distro")
		self.add_option("-V", "--cpu-vendor", dest="vendor", metavar="CPUVENDOR",
			help="set the guest flaged by cpuvendor")
		self.add_option("-w", "--whiteboard", dest="whiteboard", metavar="WHITEBOARD",
			help="append message for webUI whiteboard")
		self.add_option("-W", "--whiteboard2", dest="whiteboard2", metavar="WHITEBOARD",
			help="append message for webUI whiteboard supplied by\
user to override the default whiteboard")
		self.add_option("-x", "--pciid", dest="pciid", metavar="PCIID", 
			action="append", help="Specify the PCI ID (vendorid:partid) to look for when\
 choosing a machine")
		self.add_option("-X", "--debug", dest="debug", metavar="DEBUG",
			action="store_true", help="Turn on debug output")
		self.add_option("-y", "--types", dest="types", metavar="TYPE(s)",
			action="append", help="Include test type in selection,type from \
testdesc.info NOTE: Can not be used with -t")
		self.add_option("-Y", "--yuminstpack", dest="yuminstpack", metavar="PACKAGE", 
action="append", help="Yum install package")
		self.add_option("-z", "--memory", dest="memory", metavar="MEMORY",
			help="Specify the amount of system memory in the test machine in Megabytes")


