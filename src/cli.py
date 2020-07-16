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

from .core import OnionServer
from .sockets import UDPSocket
from .logs import Logger, StreamHandler, FileHandler
from .config import read_config
from .utils import *
from .version import __author__, __copyright__, __license__, \
                     __version__, __date__, __build__

from sys import argv
from signal import signal, SIGINT, SIGTERM


_CONFIG_FILE = '/etc/onion-ha/oniond.conf'

_USAGE = '''\
Usage: oniond [command] [options]

Commands:

    start                   Start Onion HA in an interactive mode
    check                   Check the current configuration
    status                  Show the cluster status
    version                 Show the daemon version
    about                   About Onion HA
    help                    Show this help message

Options:

    -c, --config FILE       Specify another configuration file

'start' is the default command.\
'''

_ABOUT = f'''
             o+             ≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈
             /d/              ~ Onion HA Core ~
          .h  dds.
         /h+  ddhdo.            Version: {__version__} (build {__build__})
       :yh/  -ddh/ ds.          Date:    {__date__}
     -yds`  `hdddy  dd+         Author:  {__author__}
    /ddy    yddddd+  dd+    ≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈
    hdd+   -ddddddy  ddh
    hddy   :ddddddy  ddy    {__copyright__}
    -hdds`  hddddd  hdh.    {__license__}
     `ohdh+. dddh+odh+`
       `-+syyhddys+:`       https://github.com/ValentinBELYN/OnionHA
'''

_VERSION = f'oniond {__version__} (build {__build__}) ' \
           f'released on {__date__}'


def cli():
    '''
    Runs the Onion HA command line interface.

    '''
    commands = {
        'start': start,
        'check': check,
        'status': status,
        'version': lambda _: print(_VERSION),
        'about': lambda _: print(_ABOUT),
        'help': lambda _: print(_USAGE)
    }

    arguments = argv[1:]

    if not arguments or arguments[0][0] == '-':
        command = 'start'

    else:
        command = arguments.pop(0)

    if command not in commands:
        print(f'Unknown command: {command}')
        exit(1)

    i = 0
    options = {}
    num_arguments = len(arguments)

    while i < num_arguments:
        option = arguments[i]
        value = None

        if i + 1 < num_arguments and arguments[i + 1][0] != '-':
            value = arguments[i + 1]
            i += 1

        if option in ('-c', '--config') and value:
            options['config'] = value

        i += 1

    code = commands[command](options)
    exit(code)


def start(options):
    '''
    Starts the Onion HA server on this node. This function supports
    the `config` option.

    '''
    if not is_root():
        print('Error: Onion HA does not have enough privileges to '
              'start.')
        return 1

    if is_running():
        print('Error: an instance of Onion HA is already running.')
        return 1

    if 'config' in options:
        config_file = options['config']

    else:
        config_file = _CONFIG_FILE

    config = read_config(config_file)

    if not config.is_opened:
        print('Error: unable to read the configuration file.\n\n'
              'Type \'oniond check\' to solve this error.')
        return 1

    if config.errors:
        print('Error: some settings are incorrect.\n\n'
              'Type \'oniond check\' to solve this error.')
        return 1

    if (config['general']['address'] not in
        config['cluster']['nodes']):
        print('Error: the address of this node must be entered in '
              'the \'cluster\' section of the configuration file.')
        return 1

    write_pid_file()

    if config['logging']['enable']:
        logger = Logger.get()

        logger.add_handlers(
            StreamHandler(),
            FileHandler(config['logging']['file'])
        )

        logger.level = {
            'info': Logger.INFO,
            'warning': Logger.WARN,
            'error': Logger.ERROR
        }[config['logging']['level']]

    server = OnionServer(
        address=config['general']['address'],
        port=config['cluster']['port'],
        gateway=config['general']['gateway'],
        init_delay=config['general']['initDelay'],
        deadtime=config['cluster']['deadTime'],
        node_addresses=config['cluster']['nodes'],
        action_active=config['actions']['active'],
        action_passive=config['actions']['passive'])

    signal(SIGINT, lambda *args: server.stop())
    signal(SIGTERM, lambda *args: server.stop())

    server.serve_forever()
    unlink_pid_file()

    return 0


def check(options):
    '''
    Checks the configuration file and displays potential errors. This
    function supports the `config` option.

    '''
    if 'config' in options:
        config_file = options['config']

    else:
        config_file = _CONFIG_FILE

    print('≈' * 60 + '\n',
          f'    Onion HA {__version__}',
          f'    {__copyright__}',
          f'    {__license__}\n',
          '≈' * 60 + '\n', sep='\n')

    print('Checking the configuration file:\n'
          f'    {config_file}\n')

    config = read_config(config_file)

    if not config.is_opened:
        print('The configuration file cannot be found or its syntax '
              'is wrong.')
        return 0

    if not config.errors:
        print('Your configuration file looks good!')
        return 0

    print('Some errors have been detected:\n')
    num_errors = 0

    for section in config.errors:
        print(f'    {section.upper()}\n   ',
              '-' * len(section))

        for option in config.errors[section]:
            print(f'    \u2192 {option} option is wrong')
            num_errors += 1

        print()

    print(f'Errors: {num_errors}')

    return 0


def status(options):
    '''
    Retrieves and displays the cluster status. This function supports
    the `config` option.

    '''
    if 'config' in options:
        config_file = options['config']

    else:
        config_file = _CONFIG_FILE

    config = read_config(config_file)

    if not config.is_opened or config.errors:
        print('Error: unable to read the configuration file.\n\n'
              'Type \'oniond check\' to solve this error.')
        return 1

    print('≈' * 60 + '\n',
          f'    Onion HA {__version__}',
          f'    {__copyright__}',
          f'    {__license__}\n',
          '≈' * 60 + '\n', sep='\n')

    if not is_running():
        print('Onion HA is not running.')
        return 0

    socket = UDPSocket()
    pid = get_instance_pid()

    print(f'PID: {pid}\n')

    try:
        socket.send(
            payload=b'GET STATUS',
            address='127.0.0.1',
            port=config['cluster']['port'])

        payload, address, port = socket.receive(timeout=1)
        socket.close()

    except OSError:
        print('Error: unable to retrieve the cluster status.')
        socket.close()
        return 1

    cluster_status = read_cluster_dump(payload.decode())

    status = {
        0: '[ \033[91mFAILED\033[0m ]',
        1: '[ PASSIVE ]',
        2: '[ ACTIVE ]'
    }

    i = 0
    print('Cluster status:\n')

    for address, status_code in cluster_status.items():
        i += 1
        print(f'    {i:<10} {address:20} {status[status_code]}')

    print(f'\nNodes: {i}')

    return 0
