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

from datetime import datetime


class Logger:
    '''
    A simple class for event logging. Its behavior depends on the
    registered handlers.

    :type scope: str
    :param scope: The scope of the logger.

    :type level: int
    :param level: The logging level of the created instance. Messages
        with a lower severity level will be ignored. The default level
        is `INFO`.

        * `Logger.DEBUG`: Detailed information for debugging.
        * `Logger.INFO`:  Informational messages that may be useful to
                          users.
        * `Logger.WARN`:  Potentially harmful situations.
        * `Logger.ERROR`: Error events that may affect the normal
                          program execution.

    Do not instantiate this class directly. Call the `get` method to
    create or retrieve an existing instance.

    '''
    _loggers = {}

    DEBUG = 0
    INFO  = 1
    WARN  = 2
    ERROR = 3

    def __init__(self, scope, level=1):
        self._scope = scope
        self._level = level
        self._handlers = []

    @classmethod
    def get(cls, scope='oniond'):
        '''
        Gets or creates a logger according to the specified scope. The
        default scope is `oniond`.

        '''
        if scope not in cls._loggers:
            cls._loggers[scope] = Logger(scope)

        return cls._loggers[scope]

    def add_handlers(self, *handlers):
        '''
        Adds the specified handlers to this logger.

        '''
        self._handlers.extend(handlers)

    def debug(self, message):
        '''
        Logs a message with the level `DEBUG`. The message is
        transmitted to the registered handlers.

        '''
        if self._level <= 0:
            for handler in self._handlers:
                handler.log(self._scope, 'debug', message)

    def info(self, message):
        '''
        Logs a message with the level `INFO`. The message is
        transmitted to the registered handlers.

        '''
        if self._level <= 1:
            for handler in self._handlers:
                handler.log(self._scope, 'info', message)

    def warn(self, message):
        '''
        Logs a message with the level `WARN`. The message is
        transmitted to the registered handlers.

        '''
        if self._level <= 2:
            for handler in self._handlers:
                handler.log(self._scope, 'warn', message)

    def error(self, message):
        '''
        Logs a message with the level `ERROR`. The message is
        transmitted to the registered handlers.

        '''
        if self._level <= 3:
            for handler in self._handlers:
                handler.log(self._scope, 'error', message)

    @property
    def scope(self):
        '''
        The scope of the logger.

        '''
        return self._scope

    @property
    def level(self):
        '''
        The logging level of the created instance.

        '''
        return self._level

    @level.setter
    def level(self, level):
        self._level = level


class LogHandler:
    '''
    Base class for handlers. Handler instances perform specific
    operations to log events.

    '''
    def _format(self, scope, level, message):
        '''
        Formats the message as follows:
            [date] [scope] level: message

        '''
        date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

        return f'[{date}] [{scope}] {level}: {message}'

    def log(self, scope, level, message):
        '''
        Logs an event according to the rules defined by the handler.
        May be overridden.

        '''
        pass


class StreamHandler(LogHandler):
    '''
    Handler that writes events to the standard output stream (stdout).

    '''
    def log(self, scope, level, message):
        '''
        Writes an event to the standard output.

        '''
        print(self._format(scope, level, message), flush=True)


class FileHandler(LogHandler):
    '''
    Handler that writes events to a log file.

    :type filename: str
    :param filename: The name of the log file.

    '''
    def __init__(self, filename):
        super().__init__()
        self._filename = filename

    def log(self, scope, level, message):
        '''
        Logs an event in a file.

        '''
        entry = self._format(scope, level, message)

        try:
            with open(self._filename, 'a') as file:
                file.write(entry + '\n')

        except OSError:
            pass

    @property
    def filename(self):
        '''
        The name of the log file.

        '''
        return self._filename
