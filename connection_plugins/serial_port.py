from __future__ import absolute_import

import os,sys
from ansible import errors
import serial

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class Connection(ConnectionBase):
    ''' Local serial port based connections
    For those device that don't (yet?) have a network
    '''
    has_pipelining = False
    tranport = 'serial_port'

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)
        self.serial = None

    def set_host_overrides(self, host, hostvars=None):
        ''' Override kermit-specific options from host variables.  '''
        self.port = self._play_context.port
        self.baudrate = hostvars.get('ansible_baudrate', 9600)
        self.bytesize = hostvars.get('ansible_bytesize', 8)
        self.parity = hostvars.get('ansible_parity', 'none')
        if self.parity not in ['none', 'even', 'odd', 'mark', 'space']:
            self.parity = 'none'
            #TODO: convert parity to what pyserial wants
        self.stopbits = hostvars.get('ansible_stopbits', 1)
        if self.stopbits not in [1,2]:
            self.stopbits = 1
        self.xonxoff = 0
        self.rtscts = 0
        self.timeout = None

        self._login_prompt = 'ogin:'
        self._password_prompt = 'assword:'
        self._shell_prompt = '$ '

    def _connect(self):
        ''' connect to the port '''
        super(Connection, self)._connect(self)
        self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                parity=self.parity,
                stopbits=self.stopbits,
                timeout=self.timeout,
                xonxoff=self.xonxoff,
                rtscts=self.rtscts
                )
        # TODO: log in.
        return self


    def exec_command(self, cmd, sudoable=False, in_data=None):
        ''' run a command on the device '''
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        # For now,
        if in_data:
            raise errors.AnsibleError("Internal Error: this module does not support optimized module pipelining")

        display.display("EXEC %s" % (cmd), host=self.host)

        return (p.returncode, stdout, stderr)

    def put_file(self, in_path, out_path):
        ''' transfer a file over serial from local to there '''
        # xmodem? zmodem?
        # what can I expect to be there? OR do we have to shim something?
        display.display("PUT %s TO %s" % (in_path, out_path), host=self.host)

    def fetch_file(self, in_path, out_path):
        ''' fetch a file over serial from there to local '''

        display.display("FETCH %s TO %s" % (in_path, out_path), host=self.host)

    def close(self):
        ''' terminate the connection '''
        # TODO: log out.
        self.serial.close()

#  vim: set ai et sw=4 ts=4 :
