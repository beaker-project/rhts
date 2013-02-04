# Python module
# Common rhts functions

# Copyright (c) 2005-2006 Red Hat
#
# Authors:
#       Bill Peck <bpeck@redhat.com>
#	Mike McLean <mikem@redhat.com> (upload helpers from koji)

import sys, xmlrpclib
from xmlrpclib import loads, Fault
import socket
import time
import os
import os.path
import shutil
import tempfile
import base64
import traceback

try:
    from OpenSSL.SSL import Error as ssl_error
except ImportError:
    ssl_error = socket.sslerror

def get_digest_contructor():
    dm = os.getenv('DIGEST_METHOD', 'md5').lower()
    if dm == 'md5':
        try:
            import hashlib
            return hashlib.md5
        except ImportError:
            import md5
            return md5.new
    elif dm in ('sha', 'sha1'):
        try:
            import hashlib
            return hashlib.sha1
        except ImportError:
            import sha
            return sha.new
    else:
        class NoDigest(object):
            digest_size = 0
            blocksize = 1
            def __init__(self, str=''): pass
            def update(self, str): return None
            def hexdigest(self): return ""
            def digest(self): return ""
            def copy(self): return NoDigest()
        if dm != 'no_digest':
            print "WARNING: Not recognized DIGEST_METHOD %s" % (dm,)
        return NoDigest

SCHEDULER_API = 2.2

#Exceptions
class GenericError(Exception):
    """Base class for custom exceptions"""
    faultCode = 1000
    fromFault = False
    def __str__(self):
        try:
            return str(self.args[0]['args'][0])
        except:
            try:
                return str(self.args[0])
            except:
                return str(self.__dict__)

class AuthError(GenericError):
    """Raised when there is an error in authentication"""
    faultCode = 1002

class RetryError(AuthError):
    """Raised when a request is received twice and cannot be rerun"""
    faultCode = 1009

def ensure_connection(session):
    """ This function ensures connection to the scheduler's xmlrpc server and
    does sanity check to ensure that server and client have the same API """
    try:
        ret = session.rhts.getAPIVersion()
    except:
        print "Error: Unable to connect to server %s" % session.hostname
        sys.exit(1)
    if ret != SCHEDULER_API:
        print "FAIL: The server is at API version %s and the client is at %s"  % (ret, SCHEDULER_API)
	sys.exit(1)

def encode_args(*args,**opts):
    """The function encodes optional arguments as regular arguments.

    This is used to allow optional arguments in xmlrpc calls
    Returns a tuple of args
    """
    if opts:
        opts['__starstar'] = True
        args = args + (opts,)
    return args

#A function to get create an exception from a fault
def convertFault(fault):
    """Convert a fault to the corresponding Exception type, if possible"""
    code = getattr(fault,'faultCode',None)
    if code is None:
        return fault
    for v in globals().values():
        if type(v) == type(Exception) and issubclass(v,GenericError) and \
                code == getattr(v,'faultCode',None):
            ret = v(fault.faultString)
            ret.fromFault = True
            return ret
    #otherwise...
    return fault

def callMethod(session, name, *args, **opts):
    """compatibility wrapper for _callMethod"""
    return _callMethod(session, name, args, opts)

def _callMethod(session, name, args, kwargs):
    #pass named opts in a way the server can understand
    args = encode_args(*args,**kwargs)

    tries = 0
    debug = False
    max_retries = 30
    interval = 20
    while tries <= max_retries:
        tries += 1
        try:
            result =  session.__getattr__(name)(*args)
            if result == 0:
                return True
            else:
                print result
                return False
        except Fault, fault:
            raise convertFault(fault)
        except (socket.error,socket.sslerror,xmlrpclib.ProtocolError,ssl_error), e:
            if debug:
                print "Try #%d for call (%s) failed: %s" % (tries, name, e)
        time.sleep(interval)
    raise RetryError, "reached maximum number of retries, last call failed with: %s" % ''.join(traceback.format_exception_only(*sys.exc_info()[:2]))

def uploadWrapper(session, localfile, recipetestid, name=None, callback=None, blocksize=262144, start=0):
    """upload a file in chunks using the uploadFile call"""
    # XXX - stick in a config or something
    debug = 1
    started=time.time()
    retries=3
    if name is None:
        name = os.path.basename(localfile)

    tmpfile = None
    try:
        if localfile.startswith("/sys/") or localfile.startswith("/proc/"):
            tmpfile = tempfile.mktemp() # No tempfile.mkstemp() in 2.2 (RHEL3)
            shutil.copy(localfile, tmpfile)
            localfile = tmpfile

        fo = file(localfile, "r")  #specify bufsize?
        totalsize = os.path.getsize(localfile)
        ofs = start
        if ofs != 0:
            fo.seek(ofs)
        digest_constructor = get_digest_contructor()
        digestor = digest_constructor()
        debug = False
        if callback:
            callback(0, totalsize, 0, 0, 0)
        while ofs <= totalsize:
            if (totalsize - ofs) < blocksize:
                blocksize = totalsize - ofs
            lap = time.time()
            contents = fo.read(blocksize)
            digestor.update(contents)
            size = len(contents)
            data = base64.encodestring(contents)
            if size == 0:
                # end of file, use offset = -1 to finalize upload
                offset = -1
                digest = digestor.hexdigest()
                sz = ofs
            else:
                offset = ofs
                digest = digest_constructor(contents).hexdigest()
                sz = size
            del contents
            tries = 0
            while True:
                if debug:
                    print "uploadFile(%r,%r,%r,%r,%r,...)" %(recipetestid,name,sz,digest,offset)
                if callMethod(session, 'results.uploadFile', recipetestid, name, sz, digest, offset, data):
                    break
                if tries <= retries:
                    tries += 1
                    continue
                else:
                    raise GenericError, "Error uploading file %s, offset %d" %(name, offset)
            if size == 0:
                break
            ofs += size
            now = time.time()
            t1 = now - lap
            if t1 <= 0:
                t1 = 1
            t2 = now - started
            if t2 <= 0:
                t2 = 1
            if debug:
                print "Uploaded %d bytes in %f seconds (%f kbytes/sec)" % (size,t1,size/t1/1024)
            if debug:
                print "Total: %d bytes in %f seconds (%f kbytes/sec)" % (ofs,t2,ofs/t2/1024)
            if callback:
                callback(ofs, totalsize, size, t1, t2)
        fo.close()
    finally:
        if localfile == tmpfile:
            os.unlink(tmpfile)

