''' Simple, stupid, procedural tests. 
Note: Requires a working Zabbix server

Created on Jan 12, 2014

@author: Paulson McIntyre (GpMidi) <paul@gpmidi.net>
'''

# Built-in
import logging
import time
import datetime
import threading
import random
import sys

# Others

# Ours
from mon.zbx.comm.metric import Metric
from mon.zbx.comm.zbxServer import ZabbixServer
from mon.zbx.comm.metrics import DiscoveryMetric


logging.basicConfig(
                    # level = logging.DEBUG,
                    level = 1,
                    )


def sendSimple(server,host='localhost',key='test',count=500):
    log = logging.getLogger('mon.zbx.comm._test.sendSimple')
    startTime=datetime.datetime.now()
    for i in xrange(0,count):
        metric = Metric(host = host, key = key, value = float(i * time.time() * 0.000001))
        server.queueMetric(metric=metric,priority=10)
        time.sleep(random.randint(0, 20) * 0.01)
    endTime=datetime.datetime.now()
    log.info("Done sending %d records in %r",count,endTime-startTime)
    
    
def discoveryTest(
                  server,
                  host='localhost',
                  keyD="discovery.test",
                  keyF=lambda d: 'test[%05d]'%d,
                  count=500,
                  discoveryWaitSeconds=60
                  ):
    log = logging.getLogger('mon.zbx.comm._test.discoveryTest')    
    discovd = DiscoveryMetric(key = keyD, host = host)
    for i in xrange(0,count):
        discovd.addMetric(**{
                           '{#NAME}':"Monitor " + keyF(i),
                           '{#KEY}':keyF(i),
                           '{#IDSHORT}':str(i),
                           '{#IDLONG}':"%05d" % i,
                           })
    # Send the discovered metrics
    server.queueMetric(metric = discovd, priority = 2)

    # Wait for system to discover the metrics
    time.sleep(discoveryWaitSeconds)
    
    # Send data to the metrics
    for i in xrange(0,count):
        metric = Metric(
                        host = host,
                        key = keyF(i),
                        value = time.time(),
                        )
        server.queueMetric(metric=metric,priority=10)
        time.sleep(random.randint(0, 20) * 0.01)

    log.info("Done sending %d records", count)


if __name__ == '__main__':
    log = logging.getLogger('mon.zbx.comm._test.__main__')
    try:
        import mon.zbx.comm._testSettings as settings
    except ImportError, e:
        log.exception("Failed to load settings: %r", e)
        sys.exit(1)
    server = ZabbixServer(
                        host = settings.ZABBIX_HOST,
                        port = settings.ZABBIX_PORT,
                        )
    server.start()

    # sendSimple(server, host = settings.HOST, key = settings.KEY, count = 500)

    discoveryTest(
                  server,
                  host = settings.HOST,
                  count = 10,
                  discoveryWaitSeconds = 60
                  )

    server.stopRunning()

