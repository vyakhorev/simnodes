"""
Example usage:

# print everything only to console
import lg
lg.config_logging()

# print only ConnectedToDevs to console and to a file
import lg
lg.config_logging(tofile='logs/test.log', whitelist=['DEVS'])

# hide info level
import lg
import logging
lg.config_logging(level=logging.DEBUG, whitelist=['DEVS'])

# add a logger for a module
import logging
logger = logging.getLogger(__name__)
...
# log something
logger.info('doing something')
logger.debug('doing something meaningful')
logger.warning('something strange is happening')
logger.error('that is impossible!')

"""

import logging

USE_ONLY_LAST_NAME = False # "DEVS.Node.Shop or just Shop" ?
if USE_ONLY_LAST_NAME:    # max length for console logger name (should be higher if we use full name)
    NAME_TRUNC = 50
else:
    NAME_TRUNC = 50
LEVEL_TRUNC = 4           # max length for console level name truncate

def config_logging(level=logging.INFO, toconsole=True, tofile='', whitelist=None, blacklist=None):
    """

    :param level: same meaning as in logging (applied both to file and console
    :param toconsole: set to False if you do not want the log to be in console
    :param tofile: set to file name if you want it to be printed out
    :param whitelist: set this list with strings to exclude everything other except these
    :param blacklist: exclusion list (a list with strings)
    :return: None

    """

    handlers = []

    if toconsole:
        handler = logging.StreamHandler()
        formatter_console = TableFormatter()
        handler.setFormatter(formatter_console)
        handlers += [handler]

    if tofile != '':
        handler = logging.FileHandler(tofile, mode='w') #encoding?
        # CSV format
        formatter_file = logging.Formatter('%(levelname)-10s; %(name)-20s; %(message)s;')
        handler.setFormatter(formatter_file)
        handlers += [handler]

    logging.basicConfig(level=level, handlers=handlers)

    if whitelist is not None:
        a_filter = cWhitelist(whitelist)
        for handler in logging.root.handlers:
            handler.addFilter(a_filter)

    if blacklist is not None:
        a_filter = cBlacklist(blacklist)
        for handler in logging.root.handlers:
            handler.addFilter(a_filter)

class cWhitelist(logging.Filter):
    def __init__(self, whitelist):
        super().__init__()
        self.whitelist = [logging.Filter(name) for name in whitelist]

    def filter(self, record):
        return any(f.filter(record) for f in self.whitelist)

class cBlacklist(cWhitelist):
    def filter(self, record):
        return not cWhitelist.filter(self, record)

class TableFormatter(logging.Formatter):

    def format(self, record):
        lev, nam, msg = record.levelname, record.name, record.getMessage()
        if USE_ONLY_LAST_NAME: nam = hier_trunc(nam)
        s = '[' + special_trunc(lev, LEVEL_TRUNC) + '][' + special_trunc(nam, NAME_TRUNC) + ']\tMSG: ' + msg
        return s

def special_trunc(some_str, maxlen=30):
    # truncates a string to maxlen and fills it with spaces if needed
    s = some_str[0:maxlen]
    while len(s) < maxlen:
        s += ' '
    return s

def hier_trunc(some_str):
    # Exctracts "Shop" from "DEVS.Nodes.Shop" and "Que" from "DEVS.Que."
    levels = some_str.split('.')
    if len(levels) <= 1:
        return some_str
    if levels[-1] != '':
        return levels[-1]
    if len(levels) > 1:
        return levels[-2]

