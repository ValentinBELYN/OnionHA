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

from .models import Cluster, Node, Gateway
from .sockets import UDPSocket
from .services import *
from .logs import Logger
from .version import __version__, __build__, __date__
from .utils import run_command

from time import sleep


class OnionServer:
    '''
    Onion HA is a simple way to add high availability to a cluster. In
    its latest version, Onion HA becomes more powerful, faster and
    reliable than ever, and can support an unlimited number of nodes.

    Configure the cluster according to your needs and run your own
    scripts when a node becomes active or passive.

    :type address: str
    :param address: The IP address or FQDN of the server. An IP address
        is preferred for a deterministic behavior.

    :type port: int
    :param port: The listening port of the cluster nodes, including
        this server.

    :type gateway: str
    :param gateway: The IP address or FQDN of the gateway. The gateway
        is used to check the connectivity of this node.

    :type init_delay: int
    :param init_delay: The delay before starting the server to ensure
        that the system services are operational (in seconds).

    :type deadtime: int
    :param deadtime: The delay before considering a node as dead (in
        seconds).

    :type node_addresses: list of str
    :param node_addresses: The IP address or FQDN of the nodes,
        including this node. The order of the nodes is important: in
        case of failure, their order is used to determine the new
        active node. The first node registered is the master node and
        is active by default.

    :type action_active: list of str
    :param action_active: The command or script to execute when this
        node becomes active.

    :type action_passive: list of str
    :param action_passive: The command or script to execute when this
        node becomes passive.

    '''
    def __init__(self, address, port, gateway, init_delay, deadtime,
            node_addresses, action_active, action_passive):

        self._address = address
        self._port = port
        self._gateway = gateway
        self._init_delay = init_delay
        self._deadtime = deadtime
        self._node_addresses = node_addresses
        self._action_active = action_active
        self._action_passive = action_passive
        self._is_running = False

    def _active_mode(self, node):
        '''
        Puts the server in active mode.

        '''
        logger = Logger.get()

        logger.warn(f'This node ({node.address}) is now active')

        if not run_command(self._action_active):
            logger.error('An error occurred during the execution of '
                         'your actions')

    def _passive_mode(self, node):
        '''
        Puts the server in passive mode.

        '''
        logger = Logger.get()

        logger.warn(f'This node ({node.address}) is now passive')

        if not run_command(self._action_passive):
            logger.error('An error occurred during the execution of '
                         'your actions')

    def serve_forever(self):
        '''
        Starts the Onion HA server and blocks the program until the
        `stop` method is called.

        '''
        self._is_running = True
        logger = Logger.get()

        logger.info(f'Onion HA {__version__} (build {__build__}) '
                    f'released on {__date__}')

        logger.info('Starting Onion HA...')

        socket = UDPSocket()
        cluster = Cluster()
        gateway = Gateway(0, self._gateway, self._deadtime)

        for i, address in enumerate(self._node_addresses, 1):
            node = Node(
                id=i,
                address=address,
                port=self._port,
                deadtime=self._deadtime + 1,
                is_current_node=address == self._address)

            cluster.register(node)

        services = [
            HeartbeatService(
                cluster=cluster,
                gateway=gateway,
                socket=socket),

            ConnectivityService(
                cluster=cluster,
                gateway=gateway,
                socket=socket),

            ListenerService(
                cluster=cluster,
                gateway=gateway,
                socket=socket),

            SupervisorService(
                cluster=cluster,
                gateway=gateway,
                socket=socket),
        ]

        sleep(self._init_delay)

        try:
            socket.bind('0.0.0.0', self._port)

        except OSError:
            logger.error('The specified IP address or port cannot be '
                         'assigned to the socket')
            return

        logger.info('Starting services...')

        for service in services:
            service.start()

        logger.info('Collecting information from remote nodes...')
        sleep(2)

        logger.info('Onion HA is started')

        while self._is_running:
            node = cluster.get_next_active_node()

            # We execute the actions on this node
            if node is cluster.current_node:
                if not cluster.current_node.is_active:
                    self._active_mode(cluster.current_node)

            else:
                if cluster.current_node.is_active:
                    self._passive_mode(cluster.current_node)

            # We update the status of the nodes
            if node:
                if node is not cluster.active_node:
                    cluster.activate(node)

            else:
                if cluster.active_node:
                    cluster.reset_active_node()

            sleep(0.5)

        logger.info('Stopping Onion HA...')
        sleep(1)

        if cluster.current_node.is_active:
            self._passive_mode(cluster.current_node)

        logger.info('Stopping services...')

        for service in services:
            service.shutdown()

        for service in services:
            service.join()

        socket.close()

        logger.info('Shutdown completed')

    def stop(self):
        '''
        Stops the Onion HA server. This operation is non-blocking.

        '''
        self._is_running = False

    @property
    def address(self):
        '''
        The IP address or FQDN of the server.

        '''
        return self._address

    @property
    def port(self):
        '''
        The listening port of the cluster nodes, including this server.

        '''
        return self._port

    @property
    def is_running(self):
        '''
        Indicates whether the server is running. Returns a `boolean`.

        '''
        return self._is_running
