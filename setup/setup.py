#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# +-----------------------------------------------------------------+
# | Onion HA Setup                                                  |
# |                                                                 |
# | @author:    Valentin BELYN                                      |
# | @version:   1.0 (8)                                             |
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
from subprocess import call, check_output, DEVNULL, STDOUT
from signal import signal, SIGINT, SIGTERM
from atexit import register
from time import sleep
from configparser import ConfigParser
from sys import argv as options
from pathlib import PosixPath
from os import geteuid
from platform import python_version, python_version_tuple
from shutil import unpack_archive, rmtree, copy, chown
from hashlib import sha1
from re import match


# +-----------------------------------------------------------------+
# | DESCRIPTION                                                     |
# +-----------------------------------------------------------------+
# Author and license
__author__ = 'Valentin BELYN'
__copyright__ = 'Copyright (C) 2018 Valentin BELYN'
__license__ = 'GNU General Public License v3.0'

# Version
__version__ = '1.0'
__build__ = '8'
__date__ = '2018-04-02'


# +-----------------------------------------------------------------+
# | CONSTANTS                                                       |
# +-----------------------------------------------------------------+
SETUP_FILE = 'setup.bundle'
SETUP_HASH = '5294eb616ead955e79757ac6a82c256d0f650ca2'
SETUP_COMPRESSION = 'gztar'
SETUP_EXTRACT_DIR = '/tmp/com.onion.setup'

GITHUB_WEBSITE = 'https://github.com/ValentinBELYN/OnionHA'


INSTALL_STEPS = (
    'We are preparing your environment...',
    'Installing libraries...',
    'Installing Onion...',
    'Updating your Onion configuration...',
    'Registering Onion into systemd...',
    'Initializing...'
)

UPDATE_STEPS = (
    'We are preparing your environment...',
    'Stopping the Onion daemon...',
    'Updating libraries...',
    'Updating Onion...',
    'Updating your Onion configuration...',
    'Registering Onion into systemd...',
    'Initializing...'
)

UNINSTALL_STEPS = (
    'We are preparing your environment...',
    'Stopping the Onion daemon...',
    'Uninstalling libraries...',
    'Uninstalling Onion...',
    'Removing your Onion configuration...',
    'Removing Onion from systemd...',
    'Cleaning...'
)

DELAYS = (5, 1, 0.5, 1, 2, 3, 2)


# +-----------------------------------------------------------------+
# | PROGRAM STOPPING PROCEDURE                                      |
# +-----------------------------------------------------------------+
def setup_stop(signal, frame):
    '''Program stopping procedure.'''

    # Do nothing
    return None


def setup_exit():
    '''Program stopping procedure.'''

    path_setup_dir = PosixPath(SETUP_EXTRACT_DIR)

    # Deleting installation files
    if path_setup_dir.exists() and path_setup_dir.is_dir():
        try:
            rmtree(path_setup_dir)
        except IOError:
            pass


signal(SIGINT, setup_stop)
signal(SIGTERM, setup_stop)
register(setup_exit)


# +-----------------------------------------------------------------+
# | CLASSES                                                         |
# +-----------------------------------------------------------------+
class OnionSetup(Thread):
    '''Installs, updates or uninstalls a program.'''

    def __init__(self, command):
        Thread.__init__(self)
        self.command = command

    def run(self):
        if self.command in ('update', 'uninstall'):
            path_binary_file = PosixPath(binaries_dir, binary_file)
            path_systemd_file = PosixPath(systemd_dir, systemd_file)

            # Uninstalling Onion
            call(['systemctl', 'stop', 'onion'], stdout=DEVNULL, stderr=STDOUT)
            call(['systemctl', 'disable', 'onion'], stdout=DEVNULL, stderr=STDOUT)
            path_binary_file.unlink()
            path_systemd_file.unlink()

        if self.command in ('install', 'update'):
            path_setup_dir = PosixPath(SETUP_EXTRACT_DIR)

            # Installing Onion
            vcopy(path_setup_dir / 'bin', binaries_dir)
            vcopy(path_setup_dir / 'config', config_dir)
            vcopy(path_setup_dir / 'systemd', systemd_dir)

            call(['systemctl', 'daemon-reload'], stdout=DEVNULL, stderr=STDOUT)
            call(['systemctl', 'enable', 'onion'], stdout=DEVNULL, stderr=STDOUT)

        elif self.command == 'uninstall':
            # Deleting the user configuration
            rmtree(config_dir)
            call(['systemctl', 'daemon-reload'], stdout=DEVNULL, stderr=STDOUT)


# +-----------------------------------------------------------------+
# | FUNCTIONS                                                       |
# +-----------------------------------------------------------------+
def setup_unarchive():
    '''Unarchive the setup file.'''

    path_setup_file = PosixPath(SETUP_FILE)

    if path_setup_file.exists() and path_setup_file.is_file():
        try:
            with open(path_setup_file, 'rb') as file:
                data = file.read()
                current_hash = sha1(data).hexdigest()
        except IOError:
            current_hash = ''

        if SETUP_HASH == current_hash:
            unpack_archive(SETUP_FILE, SETUP_EXTRACT_DIR, SETUP_COMPRESSION)
        else:
            print('The setup file is corrupted.')
            exit(3)
    else:
        print('The setup file cannot be found.')
        exit(3)


def setup_configuration():
    '''Retrieve the setup configuration.'''

    # str() to be compatible with Python 3.6.x
    setup_file = str(PosixPath(SETUP_EXTRACT_DIR, 'setup.conf'))

    parser = ConfigParser()
    file = parser.read(setup_file)

    # Author and version
    onion_author = parser.get('setup', 'author')
    onion_copyright = parser.get('setup', 'copyright')
    onion_license = parser.get('setup', 'license')
    onion_version = parser.get('setup', 'version')
    onion_build = int(parser.get('setup', 'build'))
    onion_date = parser.get('setup', 'date')

    # Requirements
    onion_systems_version = eval(parser.get('requirements', 'os'))
    onion_python_version = parser.get('requirements', 'python')

    # Installation directories
    binaries_dir = parser.get('install', 'bin')
    config_dir = parser.get('install', 'config')
    systemd_dir = parser.get('install', 'systemd')

    # Uninstallation settings
    binary_file = parser.get('uninstall', 'bin')
    systemd_file = parser.get('uninstall', 'systemd')

    return (
        onion_author, onion_copyright, onion_license,
        onion_version, onion_build, onion_date,
        onion_systems_version, onion_python_version,
        binaries_dir, config_dir, systemd_dir,
        binary_file, systemd_file
    )


def onion_current_version():
    '''Retrieve the installed version of Onion.'''

    path_binary_file = PosixPath(binaries_dir, binary_file)
    regex = ('^oniond (?P<version>[0-9]*\.[0-9]*(?:\.[0-9]*)?)'
             ' \(build (?P<build>[0-9]*)\)'
             ' released on (?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})$')

    if path_binary_file.exists() and path_binary_file.is_file():
        output = check_output(['oniond', 'version']).decode()
        onion_current_installation = match(regex, output)

        if onion_current_installation:
            onion_current_version = onion_current_installation['version']
            onion_current_build = int(onion_current_installation['build'])
            onion_current_date = onion_current_installation['date']

            return (
                onion_current_version,
                onion_current_build,
                onion_current_date
            )

    return False


def check_python_version():
    '''Check the Python version.'''

    python_full_version = python_version()
    python_full_version_tuple = python_version_tuple()
    python_major_version = int(python_full_version_tuple[0])
    python_minor_version = int(python_full_version_tuple[1])

    required_python_version_tuple = tuple(onion_python_version.split('.'))
    required_python_major_version = int(required_python_version_tuple[0])
    required_python_minor_version = int(required_python_version_tuple[1])

    if not (python_major_version == required_python_major_version
            and python_minor_version >= required_python_minor_version
            or python_major_version > required_python_major_version):
        print('\n\033[1;33mERROR:\033[0m Onion is not compatible'
              ' with your version of Python ({}).'.format(python_full_version),
              'Please update it before using Onion.',
              sep='\n')
        exit(5)


def vcopy(source, destination):
    '''Copy files to the specified destination.'''

    path_source = PosixPath(source)
    path_destination = PosixPath(destination)

    # Creating the destination folder if it does not exist
    if not path_destination.exists() or not path_destination.is_dir():
        path_destination.mkdir(mode=0o755)
        chown(path_destination, user=0, group=0)

    # Getting the name of the files to copy
    files = list()
    for object in path_source.iterdir():
        if object.is_file():
            filename = str(object.relative_to(path_source))

            if filename[0] != '.':
                files.append(filename)

    # Copying files
    for file in files:
        path_file_source = path_source / file
        path_file_destination = path_destination / file

        if not path_file_destination.exists() or not path_file_destination.is_file():
            copy(path_file_source, path_file_destination)
            path_file_destination.chmod(0o755)
            chown(path_file_destination, user=0, group=0)


def header(title):
    '''Display a header.'''

    call('clear')
    print('+------------------------------------------------------------+',
          '| {} |'.format(title.upper().ljust(58)),
          '+------------------------------------------------------------+',
          sep='\n', end='\n\n')


def confirm(message='Do you want to continue ?'):
    '''Display a message to confirm the user's choice.'''

    answer = input('\n{} [Y/n] '.format(message)).lower()

    if not answer or answer[0] != 'y':
        print('Aborted.')
        exit(0)


def loader(message, delay):
    '''Display a loading bar.'''

    delay = int(delay * 20)
    bars = ('|', '/', '-', '\\')

    for i in range(0, delay):
        print('{}  {}'.format(bars[i % 4], message), end='\r', flush=True)

        sleep(0.05)

    print('   {}'.format(message))


def animate(message):
    '''Animate a message.'''

    for letter in message:
        print(letter, end='', flush=True)
        sleep(0.05)

    print('\n')


# +-----------------------------------------------------------------+
# | PROGRAM STARTING PROCEDURE                                      |
# +-----------------------------------------------------------------+
def setup_install():
    '''Install Onion on the server.'''

    if onion_current_build > 0:
        print('Onion is already installed on your system.')
        exit(1)

    header('Onion will be installed on your server')
    print('         /+',
          '         .do.',
          '     .y  ccdy+.',
          '   .yys  -dds+ho.     Onion HA Engine',
          '  -yd/  -hddd:-hh:',
          '  hdh   yddddy odh    Version {} ({}) released on {}'.format(
              onion_version, onion_build, onion_date),
          '  ydd-  yddddy ydy    {}'.format(onion_author),
          '  `sdh/ :dddh:sdo`',
          '    `/oysydhso/`',
          sep='\n')

    confirm('Do you want to install Onion on this server ?')

    header('Requirements')
    print('This version of Onion requires Python {} or later.\n'.format(
        onion_python_version))

    print('These GNU/Linux distributions are officially supported:')
    for system in onion_systems_version:
        system_compatibility = '   {} {} or later.'.format(
            system['descr'].ljust(7),
            str(system['ver']).ljust(5))

        print(system_compatibility)

    check_python_version()

    confirm()

    header('Installing Onion on your system')
    print('Please wait...\n')

    onion_setup = OnionSetup('install')
    onion_setup.start()

    i = 0
    for step in INSTALL_STEPS:
        loader(step, DELAYS[i])
        i += 1

    onion_setup.join()

    header('The installation of Onion was successful')
    animate('Let\'s get started!')
    print('\nIf you like Onion, please support us on GitHub or make a donation :)',
          '   {}'.format(GITHUB_WEBSITE),
          sep='\n', end='\n\n')


def setup_update():
    '''Update Onion.'''

    if onion_current_build == 0:
        print('Onion is not installed on your system.')
        exit(1)

    elif onion_current_build >= onion_build:
        print('Onion is already up to date!',
              'Onion {} is the latest version.'.format(onion_version))
        exit(1)

    header('A newer version of Onion is available')
    print('         /+',
          '         .do.',
          '     .y  ccdy+.',
          '   .yys  -dds+ho.     Onion HA Engine',
          '  -yd/  -hddd:-hh:',
          '  hdh   yddddy odh    Version {} to {} released on {}'.format(
              onion_current_version, onion_version, onion_date),
          '  ydd-  yddddy ydy    {}'.format(onion_author),
          '  `sdh/ :dddh:sdo`',
          '    `/oysydhso/`',
          sep='\n')

    confirm('Do you want to update your Onion node ?')

    header('Requirements')
    print('This version of Onion requires Python {} or later.\n'.format(
        onion_python_version))

    print('These GNU/Linux distributions are officially supported:')
    for system in onion_systems_version:
            system_compatibility = '   {} {} or later.'.format(
                system['descr'].ljust(7),
                str(system['ver']).ljust(5))

            print(system_compatibility)

    check_python_version()

    confirm()

    header('Important')
    print('\033[1;33mThis Onion node will be stopped.\033[0m',
          'Your current configuration will be kept.',
          sep='\n')

    confirm()

    header('Updating Onion on your system')
    print('Please wait...\n')

    onion_setup = OnionSetup('update')
    onion_setup.start()

    i = 0
    for step in UPDATE_STEPS:
        loader(step, DELAYS[i])
        i += 1

    print('\nRemember to restart Onion!')
    sleep(3)

    onion_setup.join()

    header('The update of Onion was successful')
    animate('Let\'s get started!')
    print('\nIf you like Onion, please support us on GitHub or make a donation :)',
          '   {}'.format(GITHUB_WEBSITE),
          sep='\n', end='\n\n')


def setup_uninstall():
    '''Uninstall Onion.'''

    if onion_current_build == 0:
        print('Onion is not installed on your system.')
        exit(1)

    header('Onion will be uninstalled from your server')
    print('         /+',
          '         .do.',
          '     .y  ccdy+.',
          '   .yys  -dds+ho.     Onion HA Engine',
          '  -yd/  -hddd:-hh:',
          '  hdh   yddddy odh    Version {} ({}) released on {}'.format(
              onion_current_version, onion_current_build, onion_current_date),
          '  ydd-  yddddy ydy    {}'.format(onion_author),
          '  `sdh/ :dddh:sdo`',
          '    `/oysydhso/`',
          sep='\n')

    confirm('Do you want to uninstall Onion from this server ?')

    header('Important')
    print('\033[1;33mThis Onion node will be stopped.',
          'Your current configuration will be deleted.\033[0m',
          sep='\n')

    confirm()

    header('Uninstalling Onion from your system')
    print('Please wait...\n')

    onion_setup = OnionSetup('uninstall')
    onion_setup.start()

    i = 0
    for step in UNINSTALL_STEPS:
        loader(step, DELAYS[i])
        i += 1

    onion_setup.join()

    header('The uninstallation of Onion was successful')
    animate('We are sad to leave you :(')
    print('\nLeave a comment on GitHub to help us to make Onion better!',
          '   {}'.format(GITHUB_WEBSITE),
          sep='\n', end='\n\n')


def setup_license():
    '''Show the license.'''

    path_license = PosixPath(SETUP_EXTRACT_DIR, 'license.md')

    try:
        with open(path_license, 'r') as file:
            license = file.read()
            print(license)
    except IOError:
        print('The license file cannot be found.')
        exit(4)


def setup_help():
    '''Display a help message.'''

    print('Usage: setup.py [command]\n',
          'Commands:',
          '  - install     Installs Onion on the current server.',
          '  - uninstall   Uninstalls Onion and deletes your configuration.',
          '  - update      Updates your server with the latest version of Onion.',
          '  - license     Shows the license.',
          '  - help        Displays this help message.',
          sep='\n')


# Root privileges are required to continue
if geteuid() != 0:
    print('This installer does not have enough privileges to start.')
    exit(2)

# Extracting installation files
setup_unarchive()

# Retrieving the setup configuration
setup_config = setup_configuration()

onion_author, onion_copyright, onion_license, \
    onion_version, onion_build, onion_date, \
    onion_systems_version, onion_python_version, \
    binaries_dir, config_dir, systemd_dir, \
    binary_file, systemd_file = setup_config

# Retrieving the installed version of Onion
onion_current_installation = onion_current_version()

if onion_current_installation:
    onion_current_version, \
        onion_current_build, \
        onion_current_date = onion_current_installation
else:
    onion_current_build = 0

# Available options
if len(options) > 1:
    if options[1] == 'install':
        setup_install()
        exit(0)
    elif options[1] == 'uninstall':
        setup_uninstall()
        exit(0)
    elif options[1] == 'update':
        setup_update()
        exit(0)
    elif options[1] == 'license':
        setup_license()
        exit(0)
    elif options[1] == 'help':
        setup_help()
        exit(0)

print('setup.py {install|uninstall|update|license|help}')
exit(1)
