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

"""
Drop-in replacement for xmlrpclib, with added support for timeouts in the 
Server class.
"""

from xmlrpclib import *
import httplib
import sys

orig_Server = Server
def Server(url, *args, **kwargs):
   t = TimeoutTransport()
   t.timeout = kwargs.get('timeout', 20)
   if 'timeout' in kwargs:
       del kwargs['timeout']
   kwargs['transport'] = t
   server = orig_Server(url, *args, **kwargs)
   return server

class TimeoutTransport(Transport):

   def make_connection(self, host):
       if sys.version_info[:2] < (2, 7):
           conn = TimeoutHTTP(host)
           conn.set_timeout(self.timeout)
       else:
           conn = Transport.make_connection(self, host)
           if self.timeout:
               conn.timeout = self.timeout
       return conn

class TimeoutHTTPConnection(httplib.HTTPConnection):

   def connect(self):
       httplib.HTTPConnection.connect(self)
       # check whether socket timeout support is available (Python >= 2.3)
       try:
           self.sock.settimeout(self.timeout)
       except AttributeError:
           pass

class TimeoutHTTP(httplib.HTTP):
   _connection_class = TimeoutHTTPConnection

   def set_timeout(self, timeout):
       self._conn.timeout = timeout
