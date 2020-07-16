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

from .logs import Logger
from .exceptions import UnknownNodeError
from .utils import dump_cluster

from socket import timeout as TimeoutExceeded
from threading import Thread, Event
from time import sleep
from icmplib import ping


class Service(Thread):
    '''
    Onion HA is divided into several services to bring modularity in
    its development and execution.

    A service performs a specific and simple task, repeating itself
    continuously until the program stops. Each service is independent
    and cannot communicate with another.

    :type cluster: Cluster
    :param cluster: The Onion HA cluster correctly initialized.

    :type gateway: Gateway
    :param gateway: The gateway used to check the connectivity.

    :type socket: UDPSocket
    :param socket: The socket used to communicate with the other nodes
        of the cluster.

    '''
    def __init__(self, cluster, gateway, socket):
        super().__init__()
        self._cluster = cluster
        self._gateway = gateway
        self._socket = socket
        self._is_alive = True

        self._event = Event()
        self._event.set()

    def _before(self, cluster, gateway, socket):
        '''
        Actions to perform when the service starts.
        May be overridden.

        '''
        pass

    def _repeat(self, cluster, gateway, socket):
        '''
        Actions to repeat during operation of the service.
        May be overridden.

        '''
        pass

    def run(self):
        '''
        Private method. Do not override it.

        '''
        self._before(
            cluster=self._cluster,
            gateway=self._gateway,
            socket=self._socket)

        while self._is_alive:
            self._event.wait()

            self._repeat(
                cluster=self._cluster,
                gateway=self._gateway,
                socket=self._socket)

    def pause(self):
        '''
        Pauses the service.

        '''
        self._event.clear()

    def resume(self):
        '''
        Resumes the service.

        '''
        self._event.set()

    def shutdown(self):
        '''
        Permanently stops the service.
        The service must be instantiated again to be restarted.

        '''
        self._is_alive = False
        self._event.set()

    @property
    def is_alive(self):
        '''
        Indicates whether the service is alive. Returns a `boolean`.

        '''
        return self._is_alive

    @property
    def is_paused(self):
        '''
        Indicates whether the service is paused. Returns a `boolean`.

        '''
        return not self._event.is_set()


class HeartbeatService(Service):
    '''
    This service sends HELLO packets in UDP to the remote nodes to
    notify them of the existence of the current node.

    :type cluster: Cluster
    :param cluster: The Onion HA cluster correctly initialized.

    :type gateway: Gateway
    :param gateway: The gateway used to check the connectivity.

    :type socket: UDPSocket
    :param socket: The socket used to communicate with the other nodes
        of the cluster.

    '''
    def _repeat(self, cluster, gateway, socket):
        nodes = cluster.nodes

        try:
            for node in nodes:
                if node.is_current_node:
                    continue

                socket.send(
                    payload=b'HELLO',
                    address=node.address,
                    port=node.port)

        except OSError as err:
            Logger.get().debug(str(err))

        sleep(0.5)


class ConnectivityService(Service):
    '''
    This service checks the network connectivity of this node by
    sending ICMP packets to the gateway. It updates the status of the
    gateway and the current node.

    :type cluster: Cluster
    :param cluster: The Onion HA cluster correctly initialized.

    :type gateway: Gateway
    :param gateway: The gateway used to check the connectivity.

    :type socket: UDPSocket
    :param socket: The socket used to communicate with the other nodes
        of the cluster.

    '''
    def _repeat(self, cluster, gateway, socket):
        current_node = cluster.current_node

        host = ping(
            address=gateway.address,
            count=1,
            timeout=1)

        if host.is_alive:
            gateway.mark_as_alive()
            current_node.mark_as_alive()
            sleep(0.5)


class ListenerService(Service):
    '''
    This service listens to UDP datagrams sent by the remote nodes,
    processes them and updates the status of the nodes.

    Requests from hosts that are not part of the cluster are ignored
    and logged.

    :type cluster: Cluster
    :param cluster: The Onion HA cluster correctly initialized.

    :type gateway: Gateway
    :param gateway: The gateway used to check the connectivity.

    :type socket: UDPSocket
    :param socket: The socket used to communicate with the other nodes
        of the cluster.

    '''
    def _repeat(self, cluster, gateway, socket):
        try:
            payload, address, port = socket.receive()

            if (payload == b'GET STATUS' and
                address == '127.0.0.1'):
                dump = dump_cluster(cluster)

                socket.send(
                    payload=dump.encode(),
                    address=address,
                    port=port)
                return

            node = cluster.get(address)

            if payload == b'HELLO':
                node.mark_as_alive()

        except UnknownNodeError as err:
            Logger.get().warn(
                f'Possible port scan attack: request received '
                f'from an unauthorized host ({err.address})')

        except TimeoutExceeded:
            pass

        except OSError as err:
            Logger.get().debug(str(err))


class SupervisorService(Service):
    '''
    This service continually analyzes the status of the nodes and logs
    the changes.

    :type cluster: Cluster
    :param cluster: The Onion HA cluster correctly initialized.

    :type gateway: Gateway
    :param gateway: The gateway used to check the connectivity.

    :type socket: UDPSocket
    :param socket: The socket used to communicate with the other nodes
        of the cluster.

    '''
    def _before(self, cluster, gateway, socket):
        self._devices = [
            node
            for node in cluster.nodes
            if not node.is_current_node
        ]

        self._devices.append(gateway)

        self._history = {
            device.id: True
            for device in self._devices
        }

        sleep(1)

    def _repeat(self, cluster, gateway, socket):
        for device in self._devices:
            if device.is_alive is self._history[device.id]:
                continue

            if device.is_alive:
                status = 'up'

            else:
                status = 'down'

            device_name = str(device).lower()
            Logger.get().info(f'The {device_name} is {status}')
            self._history[device.id] = device.is_alive

        sleep(0.5)
