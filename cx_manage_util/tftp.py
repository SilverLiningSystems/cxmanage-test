""" Holds state about the tftp service to be used by a calxeda update
application. """

import atexit, os, signal, shutil, subprocess

from tftpy import TftpClient, TftpServer

class Tftp:
    """ Contains info about a remote or local TFTP server """

    def __init__(self):
        self._server = None
        self._client = None

        self._ipaddr = None
        self._port = None

        self._isinternal = False
        self._hasbeengood = False

        atexit.register(self.kill_server)

    def is_set(self):
        """ Return true if a server has been set """
        return self._ipaddr != None

    def is_internal(self):
        """ Return true if we're using an internal server """
        return self._isinternal

    def is_reachable(self):
        """ Attempt to reach the tftp server. Return true if the server was
        reached successfully. """
        if self._ipaddr != None:
            # Create a small file to send
            f = open("testfile_a", "w")
            f.write("")
            f.close()

            # Try sending and receiving the file
            try:
                self.put_file("testfile", "testfile_a")
                self.get_file("testfile", "testfile_b")
            except:
                pass

            # Check if we completed successfully
            os.remove("testfile_a")
            if os.path.exists("testfile_b"):
                os.remove("testfile_b")
                self._hasbeengood = True
                return True

        return False

    def set_internal_server(self, addr=None, port=0):
        """ Shut down any server that's currently running, then start an
        internal tftp server. """

        # Kill existing internal server
        self.kill_server()

        # Start tftp server
        self._server = os.fork()
        if self._server == 0:
            if not os.path.exists("tftp"):
                os.mkdir("tftp")
            server = TftpServer("tftp")
            server.listen(addr, port)
            os._exit(0)

        self._client = None

        self._ipaddr = addr

        if port != 0:
            self._port = port
        else:
            self._port = self._discover_port()

        self._isinternal = True
        self._hasbeengood = False

    def set_external_server(self, addr, port=69):
        """ Shut down any server that's currently running, then set up a
        connection to an external tftp server. """

        # Kill existing internal server
        self.kill_server()

        self._server = None
        self._client = TftpClient(self._ipaddr, self._port)

        self._ipaddr = addr
        self._port = port

        self._isinternal = False
        self._hasbeengood = False

    def restart_server(self):
        """ Reset the server model; this will also restart the server if it's
        internal. """
        if self._isinternal:
            self.set_internal_server(self._ipaddr, self._port)
        else:
            self.set_external_server(self._ipaddr, self._port)

    def kill_server(self):
        """ Kill the internal server if we're running one """
        if self._server != None:
            os.kill(self._server, signal.SIGTERM)
            self._server = None

    def get_address(self):
        """ Return the address of this server """
        return self._ipaddr

    def get_port(self):
        """ Return the listening port of this server """
        return self._port

    def get_file(self, tftppath, localpath):
        """ Download a file from the tftp server """
        try:
            if self._isinternal:
                shutil.copy("tftp/" + tftppath, localpath)
            else:
                self._client.download(tftppath, localpath)
        except:
            raise ValueError("Failed to download file from TFTP server")

    def put_file(self, tftppath, localpath):
        """ Upload a file to the tftp server """
        try:
            if self._isinternal:
                shutil.copy(localpath, "tftp/" + tftppath)
            else:
                self._client.upload(tftppath, localpath)
        except:
            raise ValueError("Failed to upload file to TFTP server")

    def _discover_port(self):
        """ Discover what port an internal server is bound to.
        This uses the 'lsof' command line utility """
        try:
            command = "lsof -p%i -a -i4" % self._server
            output = subprocess.check_output(command.split())
            return int(output.split()[-1].split(":")[-1])
        except (OSError, ValueError):
            raise ValueError("Unable to discover internal TFTP port")
