""" Holds state about the tftp service to be used by a calxeda update
application. """

from cxfwupd_resources import cxfwupd_resources

class tftp:

    def __init__(self):
        self._server = None
        self._isinternal = None
        self._hasbeengood = None

    def get_settings_str(self):
        """ Get tftp settings as a string """
        strings = cxfwupd_resources.get_strings('tftp')
        s = ''
        if not self._server:
            s = strings['not-set']
        else:
            s = self._server.get_address() + ':' + str(self._server.get_port())
            if self._isinternal:
                s += strings['internal-server']
            if not self._hasbeengood:
                res = self.is_reachable()
            if (res):
                s += strings['is-reachable']
            else:
                if self._hasbeengood:
                    s += strings['know-good-once']
                else:
                    s += strings['not-reachable']
        return s
    
    def is_reachable(self):
        """ Attempt to reach the tftp server """
        if self._server:
            # Try sending and receiving something small. if successful,
            # set _hasbeengood and return True; otherwise return False
            return True
        return False

    def set_internal_server(self, interface, port):
        self._server = TFTPInternalServer(interface, port)
        self._isinternal = True
        self._hasbeengood = False

    def set_external_server(self, addr, port):
        self._server = TFTPExternalServer(addr, port)
        self._isinternal = False
        self._hasbeengood = False
    
    def get_internal_server_interface(self):
        return self._server.get_interface()

class TFTPServer:
    def __init__(self, port):
        self._ipaddr = None
        self._port = int(port)

    def get_address(self):
        """ Return the address of the tftp server """
        return self._ipaddr
    
    def get_port(self):
        """ Return the port of the tftp server """
        return self._port

class TFTPInternalServer(TFTPServer):

    def __init__(self, interface, port):
        TFTPServer.__init__(self, port)
        self._interface = interface
        
        # TODO: start a local TFTP server
        raise NotImplementedError
    
    def get_interface(self):
        return self._interface

class TFTPExternalServer(TFTPServer):

    def __init__(self, addr, port):
        TFTPServer.__init__(self, port)
        self._ipaddr = addr
