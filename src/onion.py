#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#                                  o+
#                                  /d/
#                               .h  dds.
#                              /h+  ddhdo.
#                            :yh/  -ddh/ ds.
#                          -yds`  `hdddy  dd+
#                         /ddy    yddddd+  dd+
#                         hdd+   -ddddddy  ddh
#                         hddy   :ddddddy  ddy
#                         -hdds`  hddddd  hdh.
#                          `ohdh+. dddh+odh+`
#                            `-+syyhddys+:`
#
# +-----------------------------------------------------------------+
# | Onion HA Engine                                                 |
# |                                                                 |
# | @author:    Valentin BELYN                                      |
# | @version:   1.0.4 (27)                                          |
# |                                                                 |
# | Follow us on GitHub: https://github.com/ValentinBELYN/OnionHA   |
# +-----------------------------------------------------------------+


# +-----------------------------------------------------------------+
# | Copyright (C) 2018 Valentin BELYN.                              |
# |                                                                 |
# | This program is free software: you can redistribute it and/or   |
# | modify it under the terms of the GNU General Public License as  |
# | published by the Free Software Foundation, either version 3 of  |
# | the License, or (at your option) any later version.             |
# |                                                                 |
# | This program is distributed in the hope that it will be useful, |
# | but WITHOUT ANY WARRANTY; without even the implied warranty of  |
# | MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the   |
# | GNU General Public License for more details.                    |
# |                                                                 |
# | You should have received a copy of the GNU General Public       |
# | License along with this program.  If not, see                   |
# | <https://www.gnu.org/licenses/>.                                |
# +-----------------------------------------------------------------+


# +-----------------------------------------------------------------+
# | IMPORTS                                                         |
# +-----------------------------------------------------------------+
from threading import Thread
from subprocess import run, DEVNULL, STDOUT
from signal import signal, SIGINT, SIGTERM
from time import sleep
from datetime import datetime
from socket import gethostname
from configparser import ConfigParser
from shlex import split
from sys import argv as options
from pathlib import PosixPath
from os import geteuid, getpid


# +-----------------------------------------------------------------+
# | DESCRIPTION                                                     |
# +-----------------------------------------------------------------+
# Author and license
__author__ = 'Valentin BELYN'
__copyright__ = 'Copyright (C) 2018 Valentin BELYN'
__license__ = 'GNU General Public License v3.0'

# Version
__version__ = '1.0.4'
__build__ = '27'
__date__ = '2018-04-02'


# +-----------------------------------------------------------------+
# | CONFIGURATION                                                   |
# +-----------------------------------------------------------------+
# Onion configuration
CONFIG_FILE = '/etc/onion/onion.conf'
CONFIG_TEMPLATE = {
    'global': {
        'mode': {
            'type': 'str',
            'in': True,
            'values': ('master', 'slave'),
            'required': True
            },
        'interface': {
            'type': 'str',
            'in': False,
            'required': True
            },
        'deadTime': {
            'type': 'int',
            'min': 1,
            'max': 1000,
            'required': True
            },
        'initDelay': {
            'type': 'int',
            'min': 0,
            'max': 1000,
            'required': True
            }
        },
    'logging': {
        'enabled': {
            'type': 'str',
            'in': True,
            'values': ('yes', 'no'),
            'required': True
            },
        'file': {
            'type': 'str',
            'in': False,
            'required': False
            }
        },
    'nodes': {
        'master': {
            'type': 'str',
            'in': False,
            'required': True
            },
        'slave': {
            'type': 'str',
            'in': False,
            'required': True
            },
        'gateway': {
            'type': 'str',
            'in': False,
            'required': True
            }
        },
    'scenarios': {
        'active': {
            'type': 'str',
            'in': False,
            'required': True
            },
        'passive': {
            'type': 'str',
            'in': False,
            'required': True
            }
        }
    }

# PID information
PID = getpid()
PID_FILE = PosixPath('/var/run/oniond.pid')


# +-----------------------------------------------------------------+
# | HELP                                                            |
# +-----------------------------------------------------------------+
build = f'{__version__} (build {__build__})'

ABOUT = f'''
             o+              +-------------------------------------------+
             /d/             | Onion HA Engine                           |
          .h  dds.           +-------------------------------------------+
         /h+  ddhdo.         | Version: {build:32} |
       :yh/  -ddh/ ds.       | Release: {__date__:32} |
     -yds`  `hdddy  dd+      | Author:  {__author__:32} |
    /ddy    yddddd+  dd+     | License: {__license__:32} |
    hdd+   -ddddddy  ddh     +-------------------------------------------+
    hddy   :ddddddy  ddy
    -hdds`  hddddd  hdh.      Configuration: {CONFIG_FILE}
     `ohdh+. dddh+odh+`       Mode: {{mode}}
       `-+syyhddys+:`         Address: {{address}}
'''

HELP = '''\
Usage: oniond [command]

Commands:
    start           start Onion with the current configuration
    check           check the Onion node configuration
    version         output the version of the Onion node
    about           display all information about the daemon
    help            display this help message

\'start\' is the default command.\
'''

VERSION = f'oniond {__version__} (build {__build__}) released on {__date__}'


# +-----------------------------------------------------------------+
# | DAEMON STOPPING PROCEDURE                                       |
# +-----------------------------------------------------------------+
def onion_stop(signal, frame):
    '''Daemon stopping procedure.'''

    global onion_signal
    onion_signal = False


onion_signal = True
signal(SIGINT, onion_stop)
signal(SIGTERM, onion_stop)


# +-----------------------------------------------------------------+
# | CLASSES                                                         |
# +-----------------------------------------------------------------+
# | 1. OnionRing part                                               |
# | Checks if a host is alive                                       |
# +-----------------------------------------------------------------+
class OnionRing(Thread):
    '''* The heart of Onion *
    Checks if a host is alive.
    '''

    def __init__(self, address):
        Thread.__init__(self)
        self.address = address
        self.status = True

    def run(self):
        counter = deadtime

        while onion_signal:
            # Sending an ICMP request to the remote host and retrieving
            # the return code
            code = run(['ping', '-c', '1', '-W', '1', '-I',
                         sender_interface, self.address],
                         stdout=DEVNULL, stderr=STDOUT).returncode

            # Determine whether a host is alive or not
            # if counter = 0        -> dead
            #    counter = deadtime -> alive
            if code == 0 and counter < deadtime:
                counter = counter + deadtime / 2
            elif code > 0 and counter > 0:
                counter = max(0, counter - 1)

            # Interpretation of the result
            if counter == deadtime and not self.status:
                self.status = True
            elif counter == 0 and self.status:
                self.status = False

            # Waiting time (except in panic mode)
            if counter > 0:
                sleep(1)

    def is_alive(self):
        '''Return if the host is alive.'''

        return self.status


class OnionParser:
    '''Retrieves values from a configuration file.

    Important:
        You must import the 'configparser' module before.
    '''

    def __init__(self, filename, template):
        self.filename = filename
        self.template = template

        parser = ConfigParser()

        # Opening the configuration file
        try:
            file = parser.read(self.filename)
        except:
            file = False

        # If the file is opened
        if file:
            # Creating a dictionary that will contain the extracted configuration
            self.config = dict(self.template)
            for section in self.template:
                self.config[section] = {}
                for option in self.template[section]:
                    self.config[section][option] = 'NOT_FOUND'

            # Completion of the previously created table
            for section in self.template:
                # Checking if the section exists
                if not parser.has_section(section):
                    continue

                for option in self.template[section]:
                    # Checking if the option exists
                    if parser.has_option(section, option):
                        value = parser.get(section, option)

                        # Checking if a value is entered
                        if not value:
                            continue

                        # If the option is a STR
                        if self.template[section][option]['type'] == 'str':
                            if self.template[section][option]['in']:
                                # The string must be included in the specified values
                                if value not in self.template[section][option]['values']:
                                    continue

                        # If the option is an INT
                        elif self.template[section][option]['type'] == 'int':
                            # Trying to convert the value
                            try:
                                value = int(value)
                            except ValueError:
                                continue

                            # The number must be within the specified range
                            if (value < self.template[section][option]['min'] or
                                value > self.template[section][option]['max']):
                                continue

                        self.config[section][option] = value

                    # If the option is not specified but is optional,
                    # adding a special value
                    elif not self.template[section][option]['required']:
                        self.config[section][option] = 'NOT_SPECIFIED'
        else:
            self.config = False

    def get_config(self):
        '''Return the configuration in a dictionary.'''
        return self.config

    def get_nb_errors(self):
        '''Return the number of errors.'''

        nb_errors = 0
        if self.config:
            for section in self.config:
                for option in self.config[section]:
                    if self.config[section][option] == 'NOT_FOUND':
                        nb_errors += 1

        return nb_errors

    def add_error(self, section, option):
        '''Add an error to the specified option.'''
        self.config[section][option] = 'NOT_FOUND'


class Colors:
    '''Adds colors to a string.'''

    INFO = '\033[0m'
    WARNING = '\033[1;33m'
    CRITICAL = '\033[1;31m'
    END = '\033[0m'

    REFERENCES = {
        'INFO': INFO,
        'WARNING': WARNING,
        'CRITICAL': CRITICAL,
        'END': END
    }


# +-----------------------------------------------------------------+
# | FUNCTIONS                                                       |
# +-----------------------------------------------------------------+
def loader(message, delay):
    '''Display a loading bar.

    Examples:
        >>> loader('Processing...', 1.5)
        '|  Processing...'
    '''

    delay = int(delay * 20)
    bars = ('|', '/', '-', '\\')

    for i in range(0, delay):
        print(f'{bars[i % 4]}   {message}', end='\r', flush=True)
        sleep(0.05)


def log(level, message):
    '''Log an event.

    Examples:
        >>> log('INFO', 'Onion is starting...')
        >>> log('WARNING', 'This Onion server is passive')
        >>> log('CRITICAL', 'An error occurred while running the active scenario')
    '''

    # Displaying the message in the terminal
    # Useful for logging with systemd
    print(f'[{Colors.REFERENCES[level]}{level[0]}{Colors.END}] {message}')

    if log_enabled == 'yes':
        # Retrieving the current date
        date = datetime.today().strftime('%b %d %Y %H:%M:%S')

        # Getting the host name
        hostname = gethostname()

        # Creating the log entry
        log_entry = f'{date} {hostname} oniond {level}: {message}\n'

        try:
            with open(log_file, 'a') as file:
                file.write(log_entry)
        except IOError:
            pass


def read_configuration():
    '''Read the configuration file.'''

    # Reading the file content
    parser = OnionParser(CONFIG_FILE, CONFIG_TEMPLATE)
    config = parser.get_config()

    # If the file cannot be opened
    if not config:
        return False

    # Adding a new check to the parser
    if (config['logging']['enabled'] == 'yes' and
        config['logging']['file'] == 'NOT_SPECIFIED'):
        parser.add_error('logging', 'file')

    # If the file contains errors
    nb_errors = parser.get_nb_errors()
    if nb_errors > 0:
        return False

    # Retrieving data in variables
    server_mode = config['global']['mode']
    sender_interface = config['global']['interface']
    deadtime = config['global']['deadTime']
    init_delay = config['global']['initDelay']
    log_enabled = config['logging']['enabled']
    log_file = config['logging']['file']
    gateway_address = config['nodes']['gateway']
    scenario_active = split(config['scenarios']['active'])
    scenario_passive = split(config['scenarios']['passive'])

    # Interpretation of the results
    if server_mode == 'master':
        server_address = config['nodes']['master']
        remote_address = config['nodes']['slave']
    else:
        server_address = config['nodes']['slave']
        remote_address = config['nodes']['master']

    return (
        server_mode, sender_interface, deadtime, init_delay,
        log_enabled, log_file,
        server_address, remote_address, gateway_address,
        scenario_active, scenario_passive
    )


def set_scenario(scenario):
    '''Set the Onion scenario to active or passive.

    Examples:
        >>> set_scenario('active')
        >>> set_scenario('passive')
    '''

    log('WARNING', f'The Onion server {server_address} is {scenario}')

    try:
        if scenario == 'active':
            run(scenario_active)
        else:
            run(scenario_passive)
    except:
        log('CRITICAL', f'An error occurred while running the {scenario} scenario')


# +-----------------------------------------------------------------+
# | DAEMON STARTING PROCEDURE                                       |
# +-----------------------------------------------------------------+
def onion_check():
    '''Check the Onion node configuration.'''

    print(f'Onion HA Engine {__version__}',
          __copyright__,
          __license__,
          '\nPlease wait...\n',
          sep='\n')

    loader('Processing...', 1.5)

    # Reading the file content
    parser = OnionParser(CONFIG_FILE, CONFIG_TEMPLATE)
    config = parser.get_config()

    # If the file is opened
    if config:
        # Adding a new check to the parser
        if (config['logging']['enabled'] == 'yes' and
            config['logging']['file'] == 'NOT_SPECIFIED'):
            parser.add_error('logging', 'file')

        nb_errors = parser.get_nb_errors()

        # Displaying the configuration
        for section in config:
            print(f'    Checking the {section.capitalize()} section...')

            for option in config[section]:
                if config[section][option] == 'NOT_FOUND':
                    status = f'[ {Colors.WARNING}ERROR{Colors.END} ]'
                else:
                    status = '[ OK ]'

                print(' ' * 10 + (option + ' option').ljust(40) + status)

            print()

        # If the file contains errors
        if nb_errors > 0:
            print('Some errors have been detected.')
        else:
            print('Your configuration file looks good!')
    else:
        nb_errors = 1
        print('The configuration file cannot be found or its syntax is wrong.')

    print(f'\nErrors: {nb_errors}')


def onion_version():
    '''Output the version of the Onion node.'''

    print(VERSION)


def onion_about():
    '''Display all information about the daemon.'''

    # Reading the configuration file
    config_ext = read_configuration()

    if config_ext:
        server_mode = config_ext[0]
        server_address = config_ext[6]
    else:
        server_mode = 'unknown'
        server_address = 'unknown'

    print(ABOUT.format(mode=server_mode, address=server_address))


def onion_help():
    '''Display a help message.'''

    print(HELP)


# Available options
if len(options) > 1:
    if options[1] == 'start':
        pass
    elif options[1] == 'check':
        onion_check()
        exit(0)
    elif options[1] == 'version':
        onion_version()
        exit(0)
    elif options[1] == 'about':
        onion_about()
        exit(0)
    elif options[1] == 'help':
        onion_help()
        exit(0)
    else:
        print(f'Unknown command: {options[1]}')
        exit(1)

# Root privileges are required to continue
if geteuid() != 0:
    print('Onion does not have enough privileges to start.')
    exit(2)

# Checking if another instance of Onion is running
if PID_FILE.exists() and PID_FILE.is_file():
    print('Onion is already running.')
    exit(4)


# +-----------------------------------------------------------------+
# | MAIN PROGRAM                                                    |
# +-----------------------------------------------------------------+
# | 2. Onion HA part                                                |
# | Analyzes, logs and runs your scenarios                          |
# +-----------------------------------------------------------------+
# Reading the configuration file
config_ext = read_configuration()

if not config_ext:
    print('The configuration file cannot be opened.\n',
          'Execute \'oniond check\' to solve this error.',
          sep='\n')
    exit(3)

server_mode, sender_interface, deadtime, init_delay, \
    log_enabled, log_file, \
    server_address, remote_address, gateway_address, \
    scenario_active, scenario_passive = config_ext

# Writing the daemon PID in a file
with open(PID_FILE, 'w') as file:
    file.write(str(PID))

# Logging the start of Onion
log('INFO', 'Onion is starting...')
log('INFO', f'Version {__version__} (build {__build__}) released on {__date__}')
log('INFO', f'Using configuration at: {CONFIG_FILE}')

# Waiting before to start Onion
sleep(init_delay)

# Starting the remote host verification system OnionRing
server = OnionRing(remote_address)
gateway = OnionRing(gateway_address)
server.start()
gateway.start()

log('INFO', f'Onion is started in {server_mode} mode')

# Loop of analysis and learning
latest_scenario = 0
latest_server_status = False
latest_gateway_status = False
gateway_warning = 0

while onion_signal:
    server_status = server.is_alive()
    gateway_status = gateway.is_alive()

    # Logging equipment status
    if server_status != latest_server_status:
        latest_server_status = server_status

        if server_status:
            status_name = 'UP'
        else:
            status_name = 'DOWN'

        log('INFO', f'The remote server {remote_address} is {status_name}')

    if gateway_status != latest_gateway_status:
        latest_gateway_status = gateway_status

        if gateway_status:
            status_name = 'UP'
        else:
            status_name = 'DOWN'

        log('INFO', f'The gateway {gateway_address} is {status_name}')

    # Scenarios
    # The Onion node is master
    if server_mode == 'master':
        # 1. Scenario 1 :
        #    Remote server:  UP  <-OR->  Remote server:  DOWN
        #    Remote gateway: UP          Remote gateway: UP
        if gateway_status and latest_scenario != 1:
            latest_scenario = 1
            set_scenario('active')

        # 2. Scenario 2 :
        #    Remote server:  DOWN
        #    Remote gateway: DOWN
        elif not (server_status or gateway_status) and latest_scenario != 2:
            latest_scenario = 2
            set_scenario('passive')

    # The Onion node is slave
    else:
        # 1. Scenario 1 :
        #    Remote server:  DOWN
        #    Remote gateway: UP
        if not server_status and gateway_status and latest_scenario != 1:
            latest_scenario = 1
            set_scenario('active')

        # 2. Scenario 2 :
        #    Remote server:  UP  <-OR->  Remote server:  DOWN
        #    Remote gateway: UP          Remote gateway: DOWN
        elif (((server_status and gateway_status) or
            not (server_status or gateway_status)) and latest_scenario != 2):
            latest_scenario = 2
            set_scenario('passive')

    # 3. Scenario 3 :
    #    Remote server:  UP
    #    Remote gateway: DOWN
    if server_status and not gateway_status:
        gateway_warning += 1
        # The 'gateway_warning' variable avoids false positives if the
        # OnionRing threads are out of sync
        if gateway_warning > 2:
            log('CRITICAL', 'Onion is suspended and waits for the gateway reply')
            sleep(2.5)
    else:
        gateway_warning = 0

    sleep(0.5)

# STOPPING ONION
log('INFO', 'Onion is shutting down...')

# Waiting for the OnionRing threads to stop
server.join()
gateway.join()

# Setting the Onion mode to passive
if latest_scenario != 2:
    set_scenario('passive')
    sleep(1)

# Deleting the Onion PID file
PID_FILE.unlink()

log('INFO', 'Onion shutdown completed')
exit(0)
