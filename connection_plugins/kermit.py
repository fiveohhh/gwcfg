from __future__ import (absolute_import, division, print_function)
from __future__ import unicode_literals
__metaclass__ = type

DOCUMENTATION = '''
    connection: kermit
    short_description: connect via kermit
    description:
'''

import pexpect

from ansible.errors import AnsibleError, AnsibleConnectionFailure
from ansible.errors import AnsibleFileNotFound
from ansible.plugins.connection import ConnectionBase

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class Connection(ConnectionBase):
    ''' Connection over Kermit '''

    has_pipelining = False
    transport = 'kermit'

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)

        self.where = None
        self.pexp = None
        self._loggedin = False

    def set_host_overrides(self, host, hostvars=None):
        '''
        Override kermit-specific options from host variables.
        '''
        self.line = hostvars.get('ansible_line', '/dev/ttyS0')
        self.baudrate = hostvars.get('ansible_baudrate', 9600)
        self.bytesize = hostvars.get('ansible_bytesize', 8)
        self.parity = hostvars.get('ansible_parity', 'none')
        if self.parity not in ['none', 'even', 'odd', 'mark', 'space']:
            self.parity = 'none'
        self.stopbits = hostvars.get('ansible_stopbits', 1)
        if self.stopbits not in [1,2]:
            self.stopbits = 1
        #self.xonxoff = 0
        #self.rtscts = 0
        #self.timeout = 1
        self.remote_user = self._play_context.remote_user
        self.remote_pass = self._play_context.password
        # TODO: set these up for overriding.
        self.escape_char = '\\'
        self.kermit_cmd = 'kermit -Y'
        self.kermit_prompt = 'ermit>'
        self.remote_prompt = '[#$] ?'

    def _set_kermit_opt(self, opt, value):
        self.pexp.sendline('set %s %s' % (opt, value))
        display.vvvv("KERMIT SET %s %s" % (opt, value))
        r = self.pexp.expect([pexpect.TIMEOUT,self.kermit_prompt])
        if r == 0:
            display.error("TIMEOUT waiting for kermit prompt")
            # TODO:  reset?

    def _connect(self):
        ''' connect to the port '''
        super(Connection, self)._connect()
        display.vvv("SPAWNING %s" % (self.kermit_cmd))
        self.pexp = pexpect.spawn(self.kermit_cmd)
        r = self.pexp.expect([pexpect.TIMEOUT,self.kermit_prompt])
        if r == 0:
            display.error("TIMEOUT waiting for kermit prompt")
            raise AnsibleConnectionFailure("TIMEOUT waiting for kermit prompt")

        self._set_kermit_opt('speed', self.baudrate)
        self._set_kermit_opt('terminal bytesize', self.bytesize)
        self._set_kermit_opt('parity', self.parity)
        self._set_kermit_opt('stop-bits', self.stopbits)
        self._set_kermit_opt('carrier-watch', 'off')
        self._set_kermit_opt('line', self.line)

        self.where = 'kermit'
        self._connected = True

        self._login()

        return self

    def _switch_where(self, to='kermit'):
        ''' switch from kermit to remote or back '''
        display.vvvv("SWITCHING: from %s to %s" % (self.where, to))

        if self.where == to:
            # Nothing todo if already there.
            return
        if to == 'kermit': # Since != where, then must be from 'device'
            self.pexp.sendcontrol(self.escape_char)
            self.pexp.send('c')
            self.where = 'kermit'
            return
        if to == 'device': # Since != where, then must be from 'kermit'
            self.pexp.sendline('c')
            self.where = 'device'

    def _login(self):
        ''' Log into the device. '''
        if self._loggedin:
            return
        self._switch_where('device')
        display.vvvv("LOGGING IN")
        self.pexp.sendline('')
        r = self.pexp.expect([pexpect.TIMEOUT, 'ogin:', self.remote_prompt])
        if r == 0:
            display.error("TIMEOUT waiting to login")
            raise AnsibleConnectionFailure("TIMEOUT waiting to login")
        elif r == 1:
            self.pexp.sendline(self.remote_user)
        elif r == 2:
            # huh, looks like we're already logged in.
            self.pexp.sendline('')
            self._loggedin = True
            return

        r = self.pexp.expect([pexpect.TIMEOUT, 'assword:', self.remote_prompt])
        if r == 0:
            display.error("TIMEOUT waiting to password")
            raise AnsibleConnectionFailure("TIMEOUT waiting to login")
        elif r == 1:
            self.pexp.sendline(self.remote_password)
        elif r == 2:
            # huh, looks like we don't need a password
            self.pexp.sendline('')
            self._loggedin = True
            return

        r = self.pexp.expect([pexpect.TIMEOUT, self.remote_prompt])
        if r == 0:
            display.error("TIMEOUT waiting for shell")
            raise AnsibleConnectionFailure("TIMEOUT waiting to login")
        self.pexp.sendline('')
        self._loggedin = True

    def _logout(self):
        ''' Log out '''
        if not self._loggedin:
            return
        self._switch_where('device')
        display.vvvv("LOGGING OUT")
        self.pexp.sendline('')
        self.pexp.expect(self.remote_prompt)
        self.pexp.sendline('exit')
        self._switch_where('kermit')
        self._loggedin = False

    def exec_command(self, cmd, in_data=None, sudoable=True):
        ''' run a command on the device '''
        if not self._connected:
            self._connect()

        display.display("EXEC %s" % (cmd))

        self._switch_where('device')
        self.pexp.sendline('')
        r = self.pexp.expect([pexpect.TIMEOUT, self.remote_prompt])
        if r == 0:
            display.error("TIMEOUT waiting for shell")
            return (-42, None, None)

        self.pexp.sendline(cmd)
        r = self.pexp.expect([pexpect.TIMEOUT, self.remote_prompt])
        if r == 0:
            display.error("TIMEOUT waiting for shell")
            return (-42, None, None)

        out_data = self.pexp.before
        # TODO: get status code.
        # TODO: split stderr

        return (0, out_data, '') # (statuscode, stdout, stderr)

    def put_file(self, in_path, out_path):
        ''' transfer a file over serial from local to there '''
        # xmodem? zmodem?
        # what can I expect to be there? OR do we have to shim something?
        display.display("PUT %s TO %s" % (in_path, out_path))

    def fetch_file(self, in_path, out_path):
        ''' fetch a file over serial from there to local '''
        display.display("FETCH %s TO %s" % (in_path, out_path))

    def close(self):
        ''' terminate the connection '''
        self._logout()
        self.pexp.close()
        self._connected = False

#  vim: set ai et sw=4 ts=4 :
