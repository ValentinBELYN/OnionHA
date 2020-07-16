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


class OnionError(Exception):
    '''
    Base class for Onion HA exceptions.

    '''
    def __init__(self, message):
        self._message = message

    def __str__(self):
        return self._message

    @property
    def message(self):
        return self._message


class UnknownNodeError(OnionError):
    '''
    Raised when a cluster node cannot be found.

    '''
    def __init__(self, address):
        super().__init__(f'The node {address} does not exist')
        self._address = address

    @property
    def address(self):
        return self._address
