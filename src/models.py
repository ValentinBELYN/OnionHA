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

from time import time
from socket import getfqdn
from .exceptions import UnknownNodeError


class Cluster:
    '''
    A class that represents an Onion HA cluster, which is a collection
    of nodes.

    A cluster must contain at least two nodes and one of them must be
    the current node.

    '''
    def __init__(self):
        self._index = {}
        self._nodes = []

        self._current_node = None
        self._active_node = None

    def register(self, node):
        '''
        Registers a node in the cluster.

        The order of the nodes is important: in case of failure, their
        order is used to determine the new active node. The first node
        registered is the master node and is active by default.

        :type node: Node
        :param node: The node to add to the cluster.

        '''
        self._index[node.address] = node
        self._nodes.append(node)
        self._nodes.sort()

        if node.is_current_node:
            self._current_node = node

    def get(self, address):
        '''
        Gets the node corresponding to the specified address.

        :type address: str
        :param address: The address of the node.

        :rtype: Node
        :returns: The desired node.

        :raises UnknownNodeError: If the node cannot be found.

        '''
        source_address = address

        if address == '127.0.0.1':
            return self._current_node

        if address not in self._index:
            address = getfqdn(address)

        if address in self._index:
            return self._index[address]

        raise UnknownNodeError(source_address)

    def get_next_active_node(self):
        '''
        Gets the node with the highest priority among all the nodes
        still alive. Returns `None` if no node is alive.

        '''
        nodes = self.nodes_alive

        if nodes:
            return nodes[0]

        return None

    def activate(self, node):
        '''
        Sets a node in active mode. If a node of the cluster is already
        active, it will become passive. Indeed, only one node at a time
        can be active.

        '''
        if self._active_node:
            self._active_node.is_active = False

        node.is_active = True
        self._active_node = node

    def reset_active_node(self):
        '''
        Switches the last active node to passive mode.

        '''
        if self._active_node:
            self._active_node.is_active = False
            self._active_node = None

    @property
    def nodes(self):
        '''
        The nodes that are part of the cluster.

        '''
        return self._nodes

    @property
    def nodes_alive(self):
        '''
        The list of nodes still alive.

        '''
        return [
            node
            for node in self._nodes
            if node.is_alive
        ]

    @property
    def current_node(self):
        '''
        The current node.

        '''
        return self._current_node

    @property
    def active_node(self):
        '''
        The current active node.

        '''
        return self._active_node


class Device:
    '''
    A class that represents a simple network equipment.

    :type id: int
    :param id: The unique device identifier.

    :type address: str
    :param address: The IP address or FQDN of the device. An IP address
        is preferred for a deterministic behavior.

    :type deadtime: int
    :param deadtime: The waiting time before considering the device as
        dead (in seconds).

    '''
    def __init__(self, id, address, deadtime):
        self._id = id
        self._address = address
        self._deadtime = deadtime
        self._last_seen = 0

    def __str__(self):
        return f'{self.__class__.__name__} {self._address}'

    def __lt__(self, other):
        return self.id < other.id

    def mark_as_alive(self):
        '''
        Resets the internal countdown used to determine if the device
        is alive or not.

        '''
        self._last_seen = time()

    @property
    def id(self):
        '''
        The unique device identifier.

        '''
        return self._id

    @property
    def address(self):
        '''
        The IP address or FQDN of the device.

        '''
        return self._address

    @property
    def is_alive(self):
        '''
        Indicates whether the node is alive. Returns a `boolean`.

        '''
        return time() - self._last_seen < self._deadtime


class Gateway(Device):
    '''
    A class that represents a gateway.

    :type id: int
    :param id: The unique device identifier.

    :type address: str
    :param address: The IP address or FQDN of the device. An IP address
        is preferred for a deterministic behavior.

    :type deadtime: int
    :param deadtime: The waiting time before considering the device as
        dead (in seconds).

    '''
    def __init__(self, id, address, deadtime):
        super().__init__(id, address, deadtime)


class Node(Device):
    '''
    A class that represents a node.

    :type id: int
    :param id: The unique device identifier.

    :type address: str
    :param address: The IP address or FQDN of the device. An IP address
        is preferred for a deterministic behavior.

    :type port: int
    :param port: The listening port of the node to communicate in UDP
        with the other nodes.

    :type deadtime: int
    :param deadtime: The waiting time before considering the device as
        dead (in seconds).

    :type is_current_node: bool
    :param is_current_node: Indicates whether the node is the current
        node.

    '''
    def __init__(self, id, address, port, deadtime, is_current_node):
        super().__init__(id, address, deadtime)
        self._port = port
        self._is_current_node = is_current_node
        self._is_active = False

    @property
    def port(self):
        '''
        The listening port of the node to communicate in UDP with the
        other nodes.

        '''
        return self._port

    @property
    def is_current_node(self):
        '''
        Indicates whether the node is the current node. Returns a
        `boolean`.

        '''
        return self._is_current_node

    @property
    def is_active(self):
        '''
        Indicates whether the node is active. Returns a `boolean`.

        '''
        return self._is_active

    @is_active.setter
    def is_active(self, is_active):
        self._is_active = is_active
