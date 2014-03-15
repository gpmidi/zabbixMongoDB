''' Command Line Interface
Created on Jan 14, 2014

@author: Paulson McIntyre (GpMidi) <paul@gpmidi.net>
'''
# Built-in
import logging
import socket
from optparse import OptionParser
import datetime
import os, os.path, sys

# Others
from configobj import ConfigObj

# Ours
from mon.zbx.comm.zbxServer import ZabbixServer
from mon.zbx.www.discovery import WWWDiscoveryMetric


if __name__ == '__main__':
    log = logging.getLogger('mon.zbx.www.cmd')

    log.debug("Starting arg parsing")
    parser = OptionParser()
    parser.add_option(
                      '-b',
                      '--baselocation',
                      dest = 'baseLoc',
                      # TODO: Add support for tiered config files
                      default = os.path.expanduser(os.path.join('~','.zbxmon')),
                      action = 'store',
                      help = 'Location where logs, config files, etc are stored for this tool. [default: %default]',
                      )
    parser.add_option(
                      '-c',
                      '--cfg',
                      dest = 'configLoc',
                      # TODO: Add support for tiered config files
                      default = 'config.ini',
                      action = 'store',
                      help = 'Set config file location. [default: <baselocation>/%default]',
                      )
    parser.add_option(
                      '-v',
                      '--verbose',
                      dest = 'verboseCount',
                      # TODO: Add support for tiered config files
                      default = 0,
                      action = 'count',
                      help = 'Increase script verbosity. Use multiple times (up to 5) for more detail. ',
                      )
    parser.add_option(
                      '--logfile',
                      dest = 'logFile',
                      # TODO: Add support for tiered config files
                      default = 'mongodb-cmd.log',
                      action = 'store',
                      help = 'Set log file location. [default: <baselocation>/%default]',
                      )
    (opts, args) = parser.parse_args()
    
    # Make sure this dir exists
    try:
        if not os.path.exists(opts.baseLoc):
            os.mkdir(opts.baseLoc)
    except Exception:
        print "ERROR: Base location not found and could not create. Please manually ensure that %r exists"%opts.baseLoc    
    
    os.chdir(opts.baseLoc)

    logging.basicConfig(
                        level = 50 - (opts.verboseCount * 10),
                        filename = opts.logFile,
                        # TODO: Support file modes other than append
                        # TODO: Support both stdout and log files
                        # TODO: Support auto file rotation and compression
                        )
    log.warn("Starting www monitor tool")
    
    log.debug("Reading config file")
    # TODO: Wrap in a try/except for friendlier error messages
    # TODO: Add in options for created a nice default config file
    opts.cfg = ConfigObj(opts.configLoc)

    log.debug("Creating Zabbix server")
    server = ZabbixServer(config = opts.cfg)

    log.debug("Starting sender thread")
    server.start()
    log.debug("Started")

    m = WWWDiscoveryMetric(domainsCSV = '/root/monitor/DomainDownloadList-196756955.csv')
    server.queueMetric(m)

    log.debug("Stopping")
    server.stopRunning()

    log.warn("www monitor tool is exiting")
