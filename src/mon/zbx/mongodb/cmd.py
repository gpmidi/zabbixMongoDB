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
from mon.zbx.mongodb.discovery import MongoDBCollectionsDBDiscoveryMetric
from mon.zbx.mongodb.metrics import MongoDBCollectionStatSender, MongoDBDatabaseStatSender

# def sendSimple(server, host = 'localhost', key = 'test', count = 500):
#     log = logging.getLogger('mon.zbx.comm._test.sendSimple')
#     startTime = datetime.datetime.now()
#     for i in xrange(0, count):
#         metric = Metric(host = host, key = key, value = float(i * time.time() * 0.000001))
#         server.queueMetric(metric = metric, priority = 10)
#         time.sleep(random.randint(0, 20) * 0.01)
#     endTime = datetime.datetime.now()
#     log.info("Done sending %d records in %r", count, endTime - startTime)
#
#
# def discoveryTest(
#                   server,
#                   host = 'localhost',
#                   keyD = "discovery.test",
#                   keyF = lambda d: 'test[%05d]' % d,
#                   count = 500,
#                   discoveryWaitSeconds = 60
#                   ):
#     log = logging.getLogger('mon.zbx.comm._test.discoveryTest')
#     discovd = DiscoveryMetric(key = keyD, host = host)
#     for i in xrange(0, count):
#         discovd.addMetric(**{
#                            '{#NAME}':"Monitor " + keyF(i),
#                            '{#KEY}':keyF(i),
#                            '{#IDSHORT}':str(i),
#                            '{#IDLONG}':"%05d" % i,
#                            })
#     # Send the discovered metrics
#     server.queueMetric(metric = discovd, priority = 2)
#
#     # Wait for system to discover the metrics
#     time.sleep(discoveryWaitSeconds)
#
#     # Send data to the metrics
#     for i in xrange(0, count):
#         metric = Metric(
#                         host = host,
#                         key = keyF(i),
#                         value = time.time(),
#                         )
#         server.queueMetric(metric = metric, priority = 10)
#         time.sleep(random.randint(0, 20) * 0.01)
#
#     log.info("Done sending %d records", count)


if __name__ == '__main__':
    log = logging.getLogger('mon.zbx.mongodb.cmd')

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
    log.warn("Starting MongoDB monitor tool")
    
    log.debug("Reading config file")
    # TODO: Wrap in a try/except for friendlier error messages
    # TODO: Add in options for created a nice default config file
    opts.cfg = ConfigObj(opts.configLoc)

    log.debug("Creating Zabbix server")
    server = ZabbixServer(config = opts.cfg)

    log.debug("Starting sender thread")
    server.start()
    log.debug("Started")



    log.debug("Stopping")
    server.stopRunning()

    log.warn("MongoDB monitor tool is exiting")
