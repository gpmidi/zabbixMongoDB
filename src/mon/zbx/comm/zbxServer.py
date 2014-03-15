'''
Created on Jan 11, 2014

@author: Paulson McIntyre (GpMidi) <paul@gpmidi.net>
@author: Sergey Kirillov <https://github.com/pistolero>
@license: BSD 
@note: Originally part of https://github.com/pistolero/zbxsend/blob/master/zbxsend.py
'''
# Built-in
import time
import logging
import threading
import struct
import socket
from Queue import PriorityQueue, Empty

try:
    # Python 3.x?
    import json  # @UnresolvedImport
except:
    # Python 2.7
    import simplejson as json  # @UnresolvedImport @Reimport

# Others

# Ours
from mon.zbx.comm.metric import Metric


class ZabbixServer(threading.Thread):
    """ Allows interaction with a Zabbix server via its native server-agent protocol
    """
    CFG_SECTION = 'ZabbixServer'

    def __init__(self, config):
        """
        @param metricTimeout: How long to wait in seconds for more metrics before sending whatever is queued 
        """
        self.l = logging.getLogger(self.__class__.__module__ + "." + self.__class__.__name__)
        
        self.cfg = config
        if not self.CFG_SECTION in self.cfg.sections:
            self.cfg[self.CFG_SECTION]={}
        self.zCfg = self.cfg[self.CFG_SECTION]
        self.host = self.zCfg.get('host', '127.0.0.1')
        self.port = int(self.zCfg.get('port', '10051'))
        self.maxBatch = int(self.zCfg.get('maxBatch', '32'))
        self.metricTimeout = int(self.zCfg.get('metricTimeout', '1'))
        self.q = PriorityQueue(maxsize = int(self.zCfg.get('maxQueueSize', '100')))
        self.keepRunning = True
        if 'retryForever' in self.zCfg:
            self.retryForever = self.zCfg.as_bool('retryForever')
        else:
            self.retryForever = False
        
        assert self.port > 0 and self.port < 65536, "Invalid port number %r" % self.port

        threading.Thread.__init__(
                                  self,
                                  name = repr(self),
                                  )
        self.setDaemon(daemonic = False)

    def stopRunning(self):
        """ Gracefully stop running once the queue is empty """
        self.keepRunning=False
        
    def queueMetric(self, metric, priority = 10, block = True, timeout = None):
        """ Queue up a metric for sending to the Zabbix server
        @param priority: Dequeue priority. Lower values are sent before higher values. 
        @type priority: Int
        """
        self.l.debug("Queuing up %r to send", metric)
        assert hasattr(metric, 'toZbxJSON'), "Expected metric to have a toZbxJSON method"
        self.q.put(
                   item = (int(priority), metric),
                   block = block,
                   timeout = timeout,
                   )
        
    def __repr__(self):
        return '%s(server=%s:%d)' % (self.__class__.__name__, self.host, self.port)

    def _toZbxJSON(self,metrics=[]):
        """ Convert to JSON that Zabbix will accept """
        # Zabbix has very fragile JSON parser, and we cannot use json to dump whole packet
        return (
                '{\n'
                '\t"request":"sender data",\n'
                '\t"data":[\n%s]\n'
                '}'
                ) % (',\n'.join(map(lambda metric: metric.toZbxJSON(), metrics)))
    
    def _recv_all(self,sock, count):
        buf = ''
        while len(buf)<count:
            chunk = sock.recv(count-len(buf))
            if not chunk:
                return buf
            buf += chunk
        return buf
    
    def _sendToZabbix(self,metrics):
        """ Send the list of metrics using one connection """
        try:
            jsonData=self._toZbxJSON(metrics=metrics)        
            data_len = struct.pack('<Q', len(jsonData))
            packet = 'ZBXD\1' + data_len + jsonData
            
            zabbix = socket.socket()
            zabbix.connect((self.host, self.port))
            zabbix.sendall(packet)
            resp_hdr = self._recv_all(zabbix, 13)
            if not resp_hdr.startswith('ZBXD\1') or len(resp_hdr) != 13:
                self.l.error('Wrong zabbix response')
                return False
            resp_body_len = struct.unpack('<Q', resp_hdr[5:])[0]
            resp_body = zabbix.recv(resp_body_len)
            zabbix.close()
    
            resp = json.loads(resp_body)
            self.l.debug('Got response from Zabbix: %s' % resp)
            self.l.info(resp.get('info'))
            if resp.get('response') != 'success':
                self.l.error('Got error from Zabbix: %s', resp)
                return False
            return True
        except Exception,e:
            self.l.exception("Failed to send %d metrics with %r", len(metrics), e)
            return False

    def run(self):
        self.l.debug("Starting ZabbixServer thread %r",self.getName())
        while self.keepRunning or not self.q.empty():
            try:
                self.l.debug("Going to try to send any queued metrics")
                metrics = []
                while len(metrics) <= self.maxBatch:
                    try:
                        metric = self.q.get(block = True, timeout = self.metricTimeout)
                        # We'll take care of requeuing if this fails
                        self.q.task_done()

                        assert len(metric) == 2
                        self.l.log(3, "Dequeued %r", metric[1])
                        metrics.append(metric[1])
                    except Empty, e:
                        self.l.log(3, "Timeout reached; not waiting for more metrics")
                        break
                self.l.debug("Dequeued %d metrics", len(metrics))

                while len(metrics) > 0 and self._sendToZabbix(metrics = metrics) is False and self.retryForever:
                    self.l.debug("Retrying %d metrics", len(metrics))
            except Exception, e:
                self.l.error("Failed to catch %r", e)
                time.sleep(0.1)

        self.l.debug("Ending ZabbixServer thread %r",self.getName())



