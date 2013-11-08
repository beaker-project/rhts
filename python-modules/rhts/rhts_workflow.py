"""
Python module for generating Red Hat Test System Jobs and Recipes
"""

# Copyright (c) 2010 Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 2 of
# the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.


from types import *
from os import environ
import xmlrpclib, re
from copy import deepcopy
import xml.dom.minidom
from xml.dom.minidom import Node
import urllib2
import urllib
import httplib
import socket
import string

class RecipeMaxTimeExceeded( Exception ):
	pass

class TestExceedsRecipeMaxTime( Exception ):
	pass

def CDataNode(element, value):
	doc = xml.dom.minidom.Document()
	node = doc.createElement(element)
        node.appendChild(doc.createCDATASection(value))
	return node

def node(element, value):
	doc = xml.dom.minidom.Document()
	node = doc.createElement(element)
	node.appendChild(doc.createTextNode(value))
	return node

# We subclass ServerProxy so we can call xml-rpc methods easily
class Scheduler(xmlrpclib.ServerProxy):
	def __init__(self, hostname, testrepo, type='https'):
		if not hostname:
			hostname = "localhost"
		self.hostname = hostname
		self.testrepo = testrepo
                uri = "%s://%s/cgi-bin/rhts/scheduler_xmlrpc.cgi" % (type, hostname)
 		self.testcache = {}
		try:
			t = ProxyTransport(uri)
		except KeyError:
			t = None
		xmlrpclib.ServerProxy.__init__(self, uri, transport=t)

		self.testcache = {}

	def __deepcopy__(self, memo):
		return self

	def getTest(self,testname):
		if testname not in self.testcache.keys():
			t = self.test.get_test_by_name(testname,self.testrepo)
			if type(t) is DictType:
				self.testcache[testname] = t
		try:
			return self.testcache[testname]
		except KeyError:
			raise RuntimeError, "%s Test does not exist" % testname

	def getTestNamesByPackage(self,package):
		filter = {}
		if package:
			filter['package'] = [package]
			return self.getTestNamesByFilter(filter)
		else:
			return

	def getAllTestNames(self):
		filter = {}
		return self.getTestNamesByFilter(filter)

	def getTestNamesByFilter(self,filter):
		tests = []
		filter['test_repo'] = self.testrepo
		for test in  self.test.get_tests_by_filter(filter):
			tests.append(test['test_name'])
			if test['test_name'] not in self.testcache.keys():
				self.testcache[test['test_name']] = test
		return tests

class Job:
	def __init__(self, workflow, submitter, whiteboard):
		self.workflow = workflow
		if submitter:
			self.submitter = submitter
		else:
			self.submitter = environ["USER"]
		if whiteboard:
			self.whiteboard = whiteboard
		else:
			self.whiteboard = ""
		self.recipe_sets = []

	def __str__(self):
		out = ""
		out += "- RHTS Job -\n"
		out += "Workflow: %s\n" % (self.workflow)
		out += "Submitter: %s\n" % (self.submitter)
		out += "Whiteboard: %s\n" % (self.whiteboard)
		for rs in self.recipe_sets:
			out += "\t%s" % rs
		return out

	def __add_recipe(self, r):
		"Add a single Recipe to a RecipeSet and then add that to this Job (private method)"
		r.sched = ""
		rs = RecipeSet()
		rs.add(r)
		self.recipe_sets.append(rs)

	def __add_recipe_set(self, rs):
		"Add a single RecipeSet to this Job (private method)"
		for r in rs.recipes:
			r.sched = ""
		self.recipe_sets.append(rs)

	def add(self, rs):
		"Add a Recipe/RecipeSet or list of Recipes/RecipeSets to this Job"
		if type(rs) == InstanceType:
			if isinstance(rs, RecipeSet):
				self.__add_recipe_set(rs)
			elif isinstance(rs, Recipe):
				self.__add_recipe(rs)
			else:
				raise TypeError, "Expecing RecipeSet instance"
		elif type(rs) == ListType:
			for i in rs:
				self.add(i)
		else:
			raise TypeError, "Must pass a RecipeSet instance or list of RecipeSet instances"

	def toxml(self):
		doc = xml.dom.minidom.Document()
                job = doc.createElement("job")
		job.appendChild(node("workflow",self.workflow))
		job.appendChild(node("submitter",self.submitter))
		job.appendChild(node("whiteboard",self.whiteboard))
		for rs in self.recipe_sets:
			job.appendChild(rs.toxml())
		return job

class RecipeSet:
	def __init__(self):
		self.recipes = []

	def __str__(self):
		out = ""
		out += "-- RHTS Recipe Set --\n"
		for r in self.recipes:
			out += "\t\t%s" % r
		return out

	def __add(self, recipe):
		self.recipes.append(recipe)

	def add(self, r):
		if type(r) == InstanceType:
			if isinstance(r, Recipe):
				self.__add(r)
			else:
				raise TypeError, "Expecting Recipe instance"
		elif type(r) == ListType:
			for i in r:
				self.add(i)
		else:
			raise TypeError, "Must pass a Recipe instance, or list of Recipe instances"

	def toxml(self):
		doc = xml.dom.minidom.Document()
                recipeSet = doc.createElement("recipeSet")
		for r in self.recipes:
			recipeSet.appendChild(r.toxml())
		return recipeSet

class Recipe:
	def __init__(self, scheduler, recipe_type='machine',maxtime=0,whiteboard=''):
		self.recipe_type = recipe_type
		self.execute_script = []
		self.distro_properties = {}
		self.host_properties = []
		self.packages = []
		self.addrepos = []
		self.yuminstalls = []
		self.yumupgrades = []
		self.kernelselect = []
		self.tests = []
		self.guest_recipes = []
		self.pkgurls = []
		self.totaltime = 0
		self.maxtime = maxtime
                # machine recipe_types should only get machine system_types,
                # guest recipe_types should only get guest system_types,
                # resource recipe_types should only get resource system_types.
		self.sched = scheduler
		self.testrepo = self.sched.testrepo
		self.whiteboard = whiteboard
		self.guestname = ''
		self.guestargs = ''
                self.kickpart = ''
		self.ks = ''
		self.ba = ''
		self.dd = ''
		self.accesskey = ''
		self.reciperole = ''

		# Store metadata as a list of key, value pairs, rather than
		# a dictionary, to allow for multiple values for a key:
		self.metadata = []

	def __str__(self):
		out = ""
		out += "--- RHTS Recipe ---\n"
		out += "Recipe Role: %s\n" % (self.reciperole)
		out += "Distro Properties: %s\n" % (self.distro_properties)
		out += "Host Properties: %s\n" % (self.host_properties)
		out += "Packages: %s\n" % (' '.join(self.packages))
		out += "AddRepo(s): %s\n"% (' '.join(self.addrepos))
		out += "YumInstall(s): %s\n"% (' '.join(self.yuminstalls))
		out += "YumUpgrade(s): %s\n"% (' '.join(self.yumupgrades))
		out += "PackageUrl(s): %s\n"% (' '.join(self.pkgurls))
		out += "TestRepo: %s\n" % self.testrepo
		out += "whiteboard: %s\n" % self.whiteboard
		out += "guestname: %s\n" % self.guestname
		out += "guestargs: %s\n" % self.guestargs
                out += "kickPart: %s\n" % self.kickpart
                out += "kickstart: %s\n" % self.ks
		out += "accessKey: %s\n" % self.accesskey
		for (name, value) in self.metadata:
			out += "Metadata field: \"%s\" = \"%s\"\n" \
			       % (name, value)
		for p in self.kernelselect:
   		        out += "SelectKernel, Version:%s Variant:%s\n" % (p['version'], p['variant'])
		out += "Tests:\n"
		for (tn, tv, tr) in [(t['name'], t['vars'], t['role']) for t in self.tests]:
			out += "\t%s\n" % (tn)
			out += "\t%s\n" % (tv)
			out += "\t%s\n\n" % (tr)
		out += "-- RHTS Guest Recipe(s) --\n"
		for r in self.guest_recipes:
			out += str(r)
		return out

        def kickstart(self, ks):
		self.ks = 'RHTSNEWLINE'.join(ks.split('\n'))

	def bootargs(self, ba):
		self.ba = ba

	def driverdisk(self, dd):
		self.dd = dd

	def toxml(self):
		doc = xml.dom.minidom.Document()
                if self.recipe_type == 'machine':
                    recipe = doc.createElement("recipe")
                else:
                    recipe = doc.createElement("guestrecipe")
		if self.reciperole:
			recipe.setAttribute("reciperole", self.reciperole)
		if self.accesskey:
		    recipe.appendChild(node("accesskey", self.accesskey))
		if self.ba:
		    recipe.appendChild(node("bootargs", self.ba))
		if self.dd:
		    recipe.appendChild(node("driverdisk", self.dd))
                if self.ks:
                    recipe.appendChild(CDataNode("kickstart", "%s" % '\n'.join(self.ks.split('RHTSNEWLINE'))))
		recipe.setAttribute("testrepo", self.testrepo)
                recipe.setAttribute("whiteboard", self.whiteboard)
                if self.recipe_type == 'guest':
                    recipe.setAttribute("guestname", self.guestname)
                    recipe.setAttribute("guestargs", self.guestargs)
		for (name, value) in self.metadata:
			metadataNode = recipe.appendChild(node("metadata"))
			metadataNode.setAttribute("name", name)
			metadataNode.setAttribute("value", value)
                for yuminstall in self.yuminstalls:
                        recipe.appendChild(node("yumInstall", yuminstall))
                for yumupgrade in self.yumupgrades:
                        recipe.appendChild(node("yumUpgrade", yumupgrade))
                for package in self.packages:
                        recipe.appendChild(node("installPackage", package))
		for repo in self.addrepos:
			# Try to validate a repo.
			try:
				urllib2.urlopen("%s/repodata/repomd.xml" % repo)
			except urllib2.URLError,e:
				print "Warning: %s - double-check the Yum repo." % e
			recipe.appendChild(node("addrepo",repo))
                for key in self.distro_properties.keys():
			require = "%s = %s" % (key,self.distro_properties[key])
			recipe.appendChild(node("distroRequires",require))
                for hostRequire in self.host_properties:
			recipe.appendChild(node("hostRequires",hostRequire))
		for t in self.tests:
			test = doc.createElement("test")
			test.setAttribute("name",t['name'])
			test.setAttribute("role",t['role'])
			if t['vars']:
				params = doc.createElement("params")
				for v in t['vars']:
					key = v.split(" ")[0]
					value = string.join(v.split(" ")[1:]," ")
					param = doc.createElement("param")
					param.setAttribute("name",key)
					param.setAttribute("value",value)
					params.appendChild(param)
				test.appendChild(params)
			recipe.appendChild(test)
		for r in self.guest_recipes:
			recipe.appendChild(r.toxml())

		return recipe

	def Whiteboard(self,whiteboard):
		if whiteboard:
			self.whiteboard = whiteboard

	def InstallPackage(self, package):
		if package:
			if package not in self.packages:
				self.packages.append(package)

	def AddRepo(self,url):
		self.addrepos.append(url)

	def YumInstall(self,package):
		if package not in self.yuminstalls:
			self.yuminstalls.append(package)

	def YumUpgrade(self,package):
		if package not in self.yuminstalls:
			self.yumupgrades.append(package)

	def SelectKernel(self, version, variant):
		if version or variant:
			sk = {"version": version, "variant": variant}
			self.kernelselect.append(sk)

	def PackageURL(self, url):
		if url not in self.pkgurls:
			self.pkgurls.append(url)

        def __add_guest_recipe(self, recipe):
		recipe.recipe_type = 'guest'
		recipe.sched = ""
		test_time = 0
		for test in recipe.tests:
			test_time += test['avg_test_time']
                self.guest_recipes.append(recipe)
		return test_time

        def add_guest(self, r):
		test_time = 0
		if self.recipe_type != 'machine':
			raise TypeError, "Cannot add Guest Recipe(s) to Recipe of recipe_type %s " % self.recipe_type
                if type(r) == InstanceType:
                        if isinstance(r, Recipe):
                                test_time = self.__add_guest_recipe(r)
                        else:
                                raise TypeError, "Expecting Recipe instance"
                elif type(r) == ListType:
                        for i in r:
                                test_time += self.add_guest(i)
                else:
                        raise TypeError, "Must pass a Recipe instance, or list of Recipe instances"
		return test_time

	def guestName(self, item):
		"You must name the guest"
		self.guestname = item

	def guestArgs(self, item):
		"Add Creation arguments to Guests"
		self.guestargs = item

	def AccessKey(self, item):
		"Allows scheduling against restricted systems"
		self.accesskey = item

        def RecipeRole(self, item):
                "Specify what role this recipe will be in"
                self.reciperole = item

        def kickPart(self, item):
                "Add the partitioning string into the recipe.. "
                self.kickpart = item

	def distroTag(self, item):
		"Request a distro that has this tag"
		self.distroProperty("%s = 1" % item)

	def distroProperty(self, item):
		"set arch property that applies to both host and distro"
		(key,value) = item.split(" = ")
		if key:
			self.distro_properties[key] = value
			if key == "FAMILY":
				self.host_properties.append("FAMILY = %s" % value)
			if key == "ARCH":
				self.host_properties.append("ARCH = %s" % value)
			if key == "NAME":
				try:
					family = self.sched.test.get_distro_family(value)
				except:
					raise RuntimeError, "Failed to lookup family for tree: %s" % value
				if family:
					self.distro_properties['FAMILY'] = family
					self.host_properties.append("FAMILY = %s" % family)
				else:
					raise RuntimeError, "Failed to lookup family for tree: %s" % value

	def hostProperty(self, item):
		"Add any other key/value that applies to host selection"
		if item:
			self.host_properties.append(item)

	def __addTest(self, testname, vars=[], role='STANDALONE'):
		"Add a test (with optional variables) to the Recipe"
		try:
			test = self.sched.getTest(testname)
		except AssertionError:
			raise RuntimeError, "Test doesn't exist"
		if self.maxtime:
			if test['avg_test_time'] > self.maxtime:
				raise TestExceedsRecipeMaxTime, "%s time %s(s) exceeds Recipe max time %s(s)" % (test['test_name'],test['avg_test_time'],self.maxtime)
			if self.totaltime + test['avg_test_time'] > self.maxtime:
				raise RecipeMaxTimeExceeded, "Recipe exceeds max time"
			self.totaltime += test['avg_test_time']
		if 'ARCH' not in self.distro_properties.keys() or 'FAMILY' not in self.distro_properties.keys():
			raise RuntimeError, "Arch and/or Family is not set!"
		else:
			arch = self.distro_properties['ARCH']

		if self.distro_properties['FAMILY'] in test['families'].keys():
			arch = re.sub('^node-','', arch)
                	if arch in test['families'][self.distro_properties['FAMILY']].keys():
				self.tests.append({"id": test['id'], "name": test['test_name'], "vars": vars, "role": role, "avg_test_time": test['avg_test_time']})
				for package in test['packages_needed'].split(" "):
					self.InstallPackage(package)
				# add test Need properties here?
				return test['test_name']

	# You can call this method the following ways:
	# addTest("testname")
	# addTest("testname", vars=["arg1=val1","arg2=val2"])
	# addTest("testname", vars=["arg1=val1","arg2=val2"], "SERVER")
	# addTest({"testname" : "testname", vars : ["arg1=val1","arg2=val2"], role : "SERVER"})
	# addTest({"testname" : "testname", vars : ["arg1=val1","arg2=val2"]})
	# addTest({"testname" : "testname", role : "SERVER"})
	# addTest(tests) # tests can be an array of testnames or a dictionary
	def addTest(self, r, vars=[], role='STANDALONE'):
		t = []
                if type(r) == StringType:
                        testname = self.__addTest(r,vars,role)
			if testname:
                        	t.append(testname)
                elif type(r) == unicode:
                        testname = self.__addTest(r,vars,role)
			if testname:
                        	t.append(testname)
                elif type(r) == DictType:
			vars=[]
			role="STANDALONE"
			if "testname" in r.keys():
				if "vars" in r.keys():
					vars = r["vars"]
				if "role" in r.keys():
					role = r["role"]
				testname = self.addTest(r["testname"], vars, role)
				if testname:
                               		t.append(testname)
			else:
                        	raise KeyError, "testname not in dictionary"
                elif type(r) == ListType:
                        for i in r:
                                testname = self.addTest(i)
				if testname:
                                	t.append(testname)
                else:
                        raise TypeError, "Must pass a Test name, dictionary or list"
		return t

	def addMetadata(self, name, value):
		self.metadata.append( [name, value] )

class ProxyHTTPConnection(httplib.HTTPConnection):
	_ports = {'http' : 80, 'https' : 443}

	def request(self, method, url, body=None, headers={}):
		#request is called before connect, so can interpret url and get
		#real host/port to be used to make CONNECT request to proxy
		proto, rest = urllib.splittype(url)
		if proto is None:
			raise ValueError, "unknown URL type: %s" % url
		host, rest = urllib.splithost(rest)
		host, port = urllib.splitport(host)
		if port is None:
			try:
				port = self._ports[proto]
			except KeyError:
				raise ValueError, "unknown protocol for: %s" % url
		self._real_host = host
		self._real_port = port
		httplib.HTTPConnection.request(self, method, url, body, headers)

	def connect(self):
		httplib.HTTPConnection.connect(self)
		#send proxy CONNECT request
		self.send("CONNECT %s:%d HTTP/1.0\r\n\r\n" % (self._real_host, self._real_port))
		#expect a HTTP/1.0 200 Connection established
		response = self.response_class(self.sock, strict=self.strict, method=self._method)
		(version, code, message) = response._read_status()
		#probably here we can handle auth requests...
		if code != 200:
			#proxy returned and error, abort connection, and raise exception
			self.close()
			raise socket.error, "Proxy connection failed: %d %s" % (code, message.strip())
		#eat up header block from proxy....
		while True:
			#should not use directly fp probablu
			line = response.fp.readline()
			if line == '\r\n': break

class ProxyHTTPSConnection(ProxyHTTPConnection):
	default_port = 443

	def __init__(self, host, port = None, key_file = None, cert_file = None, strict = None):
		ProxyHTTPConnection.__init__(self, host, port)
		self.key_file = key_file
		self.cert_file = cert_file
	
	def connect(self):
		ProxyHTTPConnection.connect(self)
		#make the sock ssl-aware
		ssl = socket.ssl(self.sock, self.key_file, self.cert_file)
		self.sock = httplib.FakeSocket(self.sock, ssl)
		
class ConnectHTTPHandler(urllib2.HTTPHandler):
	def __init__(self, proxy=None, debuglevel=0):
		self.proxy = proxy
		urllib2.HTTPHandler.__init__(self, debuglevel)

	def do_open(self, http_class, req):
		if self.proxy is not None:
			req.set_proxy(self.proxy, 'http')
		return urllib2.HTTPHandler.do_open(self, ProxyHTTPConnection, req)

class ConnectHTTPSHandler(urllib2.HTTPSHandler):
	def __init__(self, proxy=None, debuglevel=0):
		self.proxy = proxy
		urllib2.HTTPSHandler.__init__(self, debuglevel)

	def do_open(self, http_class, req):
		if self.proxy is not None:
			req.set_proxy(self.proxy, 'https')
		return urllib2.HTTPSHandler.do_open(self, ProxyHTTPSConnection, req)

def get_proxy(proxies, type):
	try:
		match = re.match("(http.*://)?([-_\.A-Za-z0-9]+):(\d+)/?", proxies[type])
		if not match:
			raise Exception("Proxy format not recognised: [%s]" % proxies[type])
		proxy = "%s:%s" % (match.group(2), match.group(3))
	except KeyError:
		proxy = None
	return proxy

class ProxyTransport(xmlrpclib.Transport):
	def __init__(self, url=None):
		self._use_datetime = 0

		# determine protocol type
		self.__type, rest = urllib.splittype(url)

		# find out proxy environment
		p = get_proxy(urllib.getproxies(), self.__type)

		if p:
                    opener = urllib2.build_opener(
				ConnectHTTPHandler(proxy=p),
				ConnectHTTPSHandler(proxy=p))
		    urllib2.install_opener(opener)

	def request(self, host, handler, request_body, verbose):
		self.verbose=verbose
		url=self.__type + '://' + host + handler

		request = urllib2.Request(url)
		request.add_data(request_body)
		# Note: 'Host' and 'Content-Length' are added automatically
		request.add_header("User-Agent", self.user_agent)
		request.add_header("Content-Type", "text/xml") # Important

		f = urllib2.urlopen(request)
		return(self.parse_response(f))


