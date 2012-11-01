# Copyright (c) 2012, Calxeda Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
# * Neither the name of Calxeda Inc. nor the names of its contributors
# may be used to endorse or promote products derived from this software
# without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDERS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
# TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.


""" Holds state about the tftp service to be used by a calxeda update
application. """


import os
import sys
import atexit
import shutil
import socket
import logging
import tempfile
import traceback

from node import TFTP_DIR
from tftpy import TftpClient, TftpServer, setLogLevel
from threading import Thread
from tftpy.TftpShared import TftpException


class InternalTftp(object):
    """Definition of an Internal TFTP server."""

    def __init__(self, ip_address=None, port=0, verbose=True):
        """Creates an internal TFTP server to facilitate reading command
        responses.
        
        :param ip_address: Ip address of the Internal TFTP Server.
        :type ip_address: string
        :param port: Port for the internal TFTP Server
        :type port: integer
        :param verbose: Flag to turn on additional messaging.
        :type verbose: boolean
        """
        self.verbose = verbose
        self.tftp_dir = tempfile.mkdtemp(dir=TFTP_DIR)
        
        pipe = os.pipe()
        pid = os.fork()
        if (not pid):
            # Create a PortThread class only if needed ...
            class PortThread(Thread):
                """Thread that sends the port number through the pipe."""
                def run(self):
                    """Run function override."""
                    # Need to wait for the server to open its socket
                    while not server.sock:
                        pass
                    with os.fdopen(pipe[1], "w") as a_file:
                        a_file.write("%i\n" % server.sock.getsockname()[1])
            #
            # Create an Internal TFTP server thread 
            #
            server = TftpServer(self.tftp_dir)
            thread = PortThread()
            thread.start()
            try:
                if (self.verbose):
                    setLogLevel(logging.CRITICAL)
                # Start accepting connections ...
                server.listen(ip_address, port)
                
            except KeyboardInterrupt:
                # User @ keyboard cancelled server ...
                if (self.verbose):
                    traceback.format_exc()
            sys.exit(0)
        
        atexit.register(self.kill)
        self.server = pid
        self.ip_address = ip_address
        with os.fdopen(pipe[0]) as a_fd:
            self.port = int(a_fd.readline())

    def get_ipv4_address(self, relative_host_ip=None):
        """Returns the ipv4 address of this server.
        If this is an internal server, and we're given a relative host ip,
        then discover our address to them automatically.
        
        :param relative_host_ip: Ip address to the relative host.
        :type relative_host_ip: string
        
        :return: The ipv4 address of this InternalTftpServer.
        :rtype: string
        """
        if ((self.ip_address != None) or (relative_host_ip == None)):
            return self.ip_address
        #
        # Get our ip_address by opening a socket to the host ...
        #
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect((relative_host_ip, self.port))
        ipv4 = sock.getsockname()[0]
        sock.close()
        return ipv4
    
    def kill(self):
        """Kills the InternalTftpServer."""
        if (self.server):
            os.kill(self.server, 15)
            self.server = None

    def get_file(self, tftp_path, local_path):
        """Download a file from the tftp server to local_path.
        
        :param tftp_path: Path on the tftp_server.
        :type tftp_path: string
        :param local_path: Path (on your machine) to copy the TFTP file to.
        :type local_path: string
        """
        try:
            tftp_path = "%s/%s" % (self.tftp_dir, tftp_path)
            # Ensure the file exists ...
            with open(tftp_path) as a_file:
                a_file.close()
            shutil.copy(tftp_path, local_path)
        
        except Exception:
            traceback.format_exc()
            raise

    def put_file(self, local_path, tftp_path):
        """Upload a file from local_path to the tftp server (path).
        
        :param local_path: Path to the local file to send to the TFTP server.
        :type local_path: string
        :param tftp_path: Path to put the file to on the TFTP Server.
        :type tftp_path: string
        """
        try:
            # Ensure that the local file exists ...
            with open(local_path) as a_file:
                a_file.close()
            tftp_path = "%s/%s" % (self.tftp_dir, tftp_path)
            shutil.copy(local_path, tftp_path)
        
        except Exception:
            traceback.format_exc()
            raise


class ExternalTftp:
    """Defines a ExternalTftp server, essentially makes this class a client."""

    def __init__(self, ip_address, port=69, verbose=True):
        """Default constructor for this the ExternalTftp class.
        
        :param ip_address: Ip address of the TFTP server.
        :type ip_address: string
        :param port: Port to the External TFTP server.
        :type port: integer
        :param verbose: Flag to turn on verbose output (cmd/response).
        :type verbose: boolean
        """
        self.client = TftpClient(ip_address, port)
        self.ip_address = ip_address
        self.port = port
        self.verbose = verbose
        
        if (self.verbose):
            setLogLevel(logging.CRITICAL)

    def get_ipv4_address(self):
        """ Return the ipv4 address of the ExternalTftp server."""
        return self.ip_address

    def get_port(self):
        """ Return the listening port of this server """
        return self.port

    def get_file(self, tftppath, localpath):
        """ Download a file from the tftp server """
        try:
            self.client.download(tftppath, localpath)
            
        except TftpException:
            if (self.verbose):
                traceback.format_exc()
            raise

    def put_file(self, local_path, tftp_path):
        """ Upload a file to the tftp server """
        try:
            self.client.upload(tftp_path, local_path)
        
        except TftpException:
            if (self.verbose):
                traceback.format_exc()
            raise
