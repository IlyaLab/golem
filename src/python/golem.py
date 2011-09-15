#!/usr/bin/python
#    Copyright (C) 2003-2010 Institute for Systems Biology
#                            Seattle, Washington, USA.
# 
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
# 
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
# 
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA
# 
# 

import sys
try: import json #python 2.6 included simplejson as json
except ImportError: import simplejson as json
import httplib
import urlparse
import socket
supporttls=True
try: import ssl
except ImportError:
    supporttls=False
    print "Error importing ssl."


usage = """Usage: golem.py hostname [-p password] [-L label] [-u email] command and args
where command and args can be:
run n job_executable exeutable args : run job_executable n times with the supplied args
runlist listofjobs.txt              : run each line (n n job_executable exeutable args) of the file 
list                                : list statuses of all submissions on cluster
jobs                                : same as list
status subid                        : get status of a single submission
stop subid                          : stop a submission from submitting more jobs but let running jobs finish
kill subid                          : stop a submission from submitting more jobs and kill running jobs
nodes                               : list the nodes connected to the cluster
resize nodeid newmax                : change the number of jobs a node takes at once
restart                             : cycle all golem proccess on the cluster...use only for udating core components
die                                 : kill everything ... rarelly used
"""

class HTTPSTLSv1Connection(httplib.HTTPConnection):
        """This class allows communication via TLS, it is version of httplib.HTTPSConnection that specifies TLSv1."""

        default_port = httplib.HTTPS_PORT

        def __init__(self, host, port=None, key_file=None, cert_file=None,
                     strict=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
            httplib.HTTPConnection.__init__(self, host, port, strict, timeout)
            self.key_file = key_file
            self.cert_file = cert_file

        def connect(self):
            """Connect to a host on a given (TLS) port."""

            sock = socket.create_connection((self.host, self.port),
                                            self.timeout)
            if self._tunnel_host:
                self.sock = sock
                self._tunnel()
            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, False,ssl.CERT_NONE,ssl.PROTOCOL_TLSv1)


def encode_multipart_formdata(data, filebody):
    """multipart encodes a form. data should be a dictionary of the the form fields and filebody
	should be a string of the body of the file"""
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    L = []
    for key, value in data.iteritems():
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    if filebody != "":
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="jsonfile"; filename="data.json"')
        L.append('Content-Type: text/plain')
        L.append('')
        L.append(filebody)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body


def doGet(url, loud=True):
    """
    posts a GET request to url
    """
    u = urlparse.urlparse(url)
    if u.scheme == "http":
        conn = httplib.HTTPConnection(u.hostname,u.port)
    else:

        conn = HTTPSTLSv1Connection(u.hostname,u.port)#,privateKey=key,certChain=X509CertChain([cert]))
    
        
    conn.request("GET", u.path)

    resp = conn.getresponse()
    output = None
    if resp.status == 200:
        output = resp.read()
        if loud:
            try:
                print json.dumps(json.JSONDecoder().decode(output), sort_keys=True, indent=4)
            except:
                print output
    elif loud:
        print resp.status, resp.reason

    return resp, output
    #conn.close()

def doPost(url, paramMap, jsondata,password, loud=True, label="", email=""):
    """
    posts a multipart form to url, paramMap should be a dictionary of the form fields, json data
    should be a string of the body of the file (json in our case) and password should be the password
    to include in the header
    """

    u = urlparse.urlparse(url)
    
    content_type, body =encode_multipart_formdata(paramMap,jsondata)
    headers = { "Content-type": content_type,
        'content-length':str(len(body)),
        "Accept": "text/plain",
        "x-golem-apikey":password,
		"x-golem-job-label": label,
		"x-golem-job-owner": email
    }


    if loud: print "scheme: %s host: %s port: %s"%(u.scheme, u.hostname, u.port)
    

    if u.scheme == "http":
        conn = httplib.HTTPConnection(u.hostname,u.port)
    else:

        conn = HTTPSTLSv1Connection(u.hostname,u.port)#,privateKey=key,certChain=X509CertChain([cert]))
    
        
    conn.request("POST", u.path, body, headers)

    output = None
    resp = conn.getresponse()
    if resp.status == 200:
        output = resp.read()
        if loud:
            try:
                print json.dumps(json.JSONDecoder().decode(output), sort_keys=True, indent=4)
            except:
                print output
    elif loud:
        print resp.status, resp.reason

    return resp, output
    #conn.close()


def canonizeMaster(master, loud = True):
    """Attaches an http or https prefix onto the master connection string if needed.
    """
    if master[0:4] != "http":
        if supporttls:
            if loud: print "Using https."
            canonicalMaster = "https://" + master
        else:
            if loud: print "Using http (insecure)."
            canonicalMaster = "http://" + master
    if canonicalMaster[0:5] == "https" and supporttls == False:
        raise ValueError("HTTPS specified, but the SSL package tlslite is not available. Install tlslite.")
    return canonicalMaster


def runOneLine(count, args, pwd, url, label="", email="", loud = True):
    """
    Runs a single command on a specified Golem cluster.
    Parameters:
        count - Number of times to run the command.
        args - Argument list to the command, including the command itself and all parameters.
        pwd - password to the Golem server.
        url - URL to the Golem server.
        label - optional header to label job
        email - optional email to indicate ownership
        loud - whether or not to print status messages on stdout. Defaults to True.
    Returns:
        A 2-tuple of the Golem server's response number and the body of the response.
    Throws:
        Any failure of the HTTP channel will go uncaught.
    """
    jobs = [{"Count": int(count), "Args": args}]
    jobs = json.dumps(jobs)
    data = {'command': "run"}
    if loud : print "Submitting run request to %s." % url
    return doPost(url, data, jobs, pwd, loud, label, email)


def generateJobList(fo):
    """Generator that produces a sequence of job dicts from a runlist file. More efficient than list approach.
    """
    for line in fo:
        values = line.split()
        yield {"Count": int(values[0]), "Args": values[1:]}


def runBatch(jobs, pwd, url, loud=True, label="", email=""):
    """
    Runs a Python list of jobs on the specified Golem cluster.
    Parameters:
        jobs - iterable sequence of dict-like objects fitting the job schema. Keys are of type string:
            "Count" - integer representing the number of times to run this job
            "Args" - list of strings representing the command line to run, including executable
        pwd - password for the Golem server
        url - URL to reach the Golem server, including protocol and port
        label - optional header to label job
        email - optional email to indicate ownership
        loud - whether to print status messages on stdout. Defaults to True.
    Returns:
        A 2-tuple of the Golem server's response number and the body of the response.
    Throws:
        Any failure of the HTTP channel will go uncaught.
    """
    jobs = json.dumps([job for job in jobs])
    data = {'command': "runlist"}
    if loud: print "Submitting run request to %s." % url
    return doPost(url, data, jobs, pwd, loud, label, email)


def runList(fo, pwd, url, loud = True, label="", email=""):
    """
    Interprets an open file as a runlist, then executes it on the specified Golem cluster.
    Parameters:
        fo - Readable open file-like-object representing a runlist.
        pwd - password for the Golem server
        url - URL to reach the Golem server, including protocol and port
        label - optional header to label job
        email - optional email to indicate ownership
        loud - whether to print status messages on stdout. Defaults to True.
    Returns:
        A 2-tuple of the Golem server's response number and the body of the response.
    Throws:
        Any failure of the HTTP channel will go uncaught.
    """
    jobs = generateJobList(fo)
    return runBatch(jobs, pwd, url, label, email, loud)


def runOnEach(jobs, pwd, url, loud=True, label="", email=""):
    """
    Runs a single job on each machine in a Golem cluster.
    Parameters:
        jobs - a single dict fitting the job schema. Keys are of type string:
            "Count" - integer representing the number of times to run this job
            "Args" - list of strings representing the command line to run, including executable
        pwd - the password for the Golem server
        url - URL to reach the Golem server, including protocol and port
        label - optional header to label job
        email - optional email to indicate ownership
        loud - whether to print status messages on stdout. Defaults to True.
    Returns:
        A 2-tuple of the Golem server's response number and the body of the response.
    Throws:
        Any failure of the HTTP channel will go uncaught.
    """
    jobs = json.dumps(jobs)
    data = {'command': "runoneach"}
    print "Submitting run request to %s." % url
    return doPost(url, data, jobs, pwd, loud, label, email)


def getJobList(url, loud=True):
    """
    Queries the Golem server for the list of current and previous jobs.
    Parameters:
        url - URL to reach the Golem server, including protocol and port
        loud - whether to print the response on stdout. Defaults to True.
    Returns:
        A 2-tuple of the Golem server's response number and the body of the response.
    Throws:
        Any failure of the HTTP channel will go uncaught.
    """
    return doGet(url, loud)


def stopJob(jobId, pwd, url, loud = True):
    """Stop a job identified by ID.
    Parameters:
        jobId - String of the ID of job to stop
        pwd - password for the Golem server
        url - URL to reach the Golem server, including protocol and port
        loud - whether to print the response on stdout. Defualts to True.
    Returns:
        A 2-tuple of the Golem server's response number and the body of the response.
    Throws:
        Any failure of the HTTP channel will go uncaught.
    """
    return doPost(url + jobId + "/stop", {}, "", pwd, loud, "", "")


def killJob(jobId, pwd, url, loud=True):
    """
    Kill a job identified by ID.
    Parameters:
        jobId - String of the ID of job to kill
        pwd - password for the Golem server
        url - URL to reach the Golem server, including protocol and port
        loud - whether to print the response on stdout. Defualts to True.
    Returns:
        A 2-tuple of the Golem server's response number and the body of the response.
    Throws:
        Any failure of the HTTP channel will go uncaught.
    """
    return doPost(url + jobId + "/kill", {}, "", pwd, loud, "", "")


def getJobStatus(jobId, url, loud=True):
    """
    Queries the Golem server for the status of a particular job.
    Parameters:
        jobID - String of the ID of job to kill
        url - URL to reach the Golem server, including protocol and port
        loud - whether to print the response on stdout. Defaults to True.
    Returns:
        A 2-tuple of the Golem server's response number and the body of the response.
    Throws:
        Any failure of the HTTP channel will go uncaught.
    """
    return doGet(url + jobId, loud)


def getNodesStatus(master, loud=True):
    """
    Queries the golem server for the status of its nodes.
    Parameters:
        master - URL to reach the Golem server, including protocol and port
        loud - whether to print the response to stdout. Defaults to True.
    Returns:
        A 2-tuple of the Golem server's response number and the body of the response.
    Throws:
        Any failure of the HTTP channel will go uncaught.
    """
    return doGet(master + "/nodes/", loud)


def main():
    """
    Parses argv and performs the user-specified commands. See usage info.

    Called if __name___ == "__main__". Not really intended to be called otherwise. Hardwired to reference sys.argv.
    """
    if len(sys.argv)==1:
        print usage
        return
        
    master = sys.argv[1]
    commandIndex = 2
    pwd = ""
    label = ""
    email = ""

    if sys.argv[commandIndex] == "-p":
        pwd = sys.argv[commandIndex+1]
        commandIndex = commandIndex+2

    if sys.argv[commandIndex] == "-L":
        label = sys.argv[commandIndex+1]
        commandIndex = commandIndex+2

    if sys.argv[commandIndex] == "-u":
        email = sys.argv[commandIndex+1]
        commandIndex = commandIndex+2

    cmd = sys.argv[commandIndex].lower()

    master = canonizeMaster(master)
    
    url = master+"/jobs/"

    if cmd == "run":
        runOneLine(int(sys.argv[commandIndex+1]), sys.argv[commandIndex+2:], pwd, url, True, label, email)
    elif cmd == "runlist":
        runList(open(sys.argv[commandIndex + 1]), pwd, url, True, label, email)
    elif cmd == "runoneach":
        jobs = [{"Args": sys.argv[commandIndex + 1:]}]
        runOnEach(jobs, pwd, url, True, label, email)
    elif cmd == "jobs" or cmd == "list":
        getJobList(url)
    elif cmd == "stop":
        jobId = sys.argv[commandIndex+1]
        stopJob(jobId, pwd, url)
    elif cmd == "kill":
        jobId = sys.argv[commandIndex+1]
        killJob(jobId, pwd, url)
    elif cmd == "status":
        jobId = sys.argv[commandIndex+1]
        getJobStatus(jobId, url)
    elif cmd == "nodes":
        getNodesStatus(master)
    elif cmd == "resize":
        #TODO refactor once I understand what this does
        doPost(master+"/nodes/"+sys.argv[commandIndex+1]+"/resize/"+sys.argv[commandIndex+2],{},"",pwd)
    elif cmd == "restart":
        input = raw_input("This will kill all jobs on the cluster and is only used for updating golem version. Enter \"Y\" to continue.>")
        if input == "Y":
            doPost(master+"/nodes/restart",{},"",pwd)
        else:
            print "Canceled"
    elif cmd == "die":
        input = raw_input("This kill the entire cluster down and is almost never used. Enter \"Y\" to continue.>")
        if input == "Y":
            doPost(master+"/nodes/die",{},"",pwd)
        else:
            print "Canceled"


if __name__ == "__main__":
    main()