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

from configpilot import ConfigPilot, OptionSpec
from .utils import parse_command


_OPTIONS = [
    # General
    OptionSpec(
        section='general',
        option='address'
    ),

    OptionSpec(
        section='general',
        option='gateway'
    ),

    OptionSpec(
        section='general',
        option='initDelay',
        allowed=range(0, 3600),
        type=int
    ),

    # Logging
    OptionSpec(
        section='logging',
        option='enable',
        type=bool
    ),

    OptionSpec(
        section='logging',
        option='level',
        allowed=('info', 'warning', 'error'),
        default='info'
    ),

    OptionSpec(
        section='logging',
        option='file',
        default='/var/log/oniond.log'
    ),

    # Cluster
    OptionSpec(
        section='cluster',
        option='port',
        allowed=range(1024, 49151),
        type=int
    ),

    OptionSpec(
        section='cluster',
        option='deadTime',
        allowed=range(2, 3600),
        type=int
    ),

    OptionSpec(
        section='cluster',
        option='nodes',
        type=[str]
    ),

    # Actions
    OptionSpec(
        section='actions',
        option='active',
        type=parse_command
    ),

    OptionSpec(
        section='actions',
        option='passive',
        type=parse_command
    )
]


def read_config(file):
    '''
    Reads and parses an Onion HA configuration file.

    '''
    config = ConfigPilot()
    config.register(*_OPTIONS)
    config.read(file)

    return config
