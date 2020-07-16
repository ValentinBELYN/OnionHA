'''
    OnionHA
    ~~~~~~~

        https://github.com/ValentinBELYN/OnionHA

    :copyright: Copyright 2017-2020 Valentin BELYN.
    :license: GNU GPLv3, see the LICENSE for details.

    ~~~~~~~

    This program is free software: you can redistribute it and/or
    modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see
    <https://www.gnu.org/licenses/>.
'''

import socket


class UDPSocket:
    '''
    A class that simplifies the use of UDP sockets.

    '''
    def __init__(self):
        self._address = None
        self._port = None

        self._socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM)

        self._socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            True)

    def bind(self, address, port):
        '''
        Assigns the specified address and port to the socket.

        '''
        self._address = address
        self._port = port
        self._socket.bind((address, port))

    def send(self, payload, address, port):
        '''
        Sends the payload (in bytes) to the destination address.

        '''
        return self._socket.sendto(payload, (address, port))

    def receive(self, timeout=5, buffer_size=1024):
        '''
        Reads incoming data from this socket and returns a tuple with
        the payload, the address and the source port.

        '''
        self._socket.settimeout(timeout)
        packet = self._socket.recvfrom(buffer_size)

        payload = packet[0]
        address = packet[1][0]
        port = packet[1][1]

        return payload, address, port

    def close(self):
        '''
        Close the socket. It cannot be used after this call.

        '''
        self._socket.close()

    @property
    def address(self):
        '''
        The address of the socket. Returns `None` if the `bind` method
        was not called.

        '''
        return self._address

    @property
    def port(self):
        '''
        The port of the socket. Returns `None` if the `bind` method was
        not called.

        '''
        return self._port
