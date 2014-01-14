'''
Created on Jan 11, 2014

@author: Paulson McIntyre (GpMidi) <paul@gpmidi.net>
@author: Sergey Kirillov <https://github.com/pistolero>
@license: BSD 
@note: Originally part of https://github.com/pistolero/zbxsend/blob/master/zbxsend.py
'''
import time
import logging
import socket
try:
    import json  # @UnresolvedImport
except:
    import simplejson as json  # @UnresolvedImport @Reimport


class Metric(object):
    """ A Zabbix metric data point 
    """
    DEFAULT_KEY = lambda metric: None
    DEFAULT_VALUE = lambda metric: None
    DEFAULT_HOST = lambda metric: socket.getfqdn()

    def __init__(self, key = None, value = None, host = None, clock = None):
        self.l = logging.getLogger(self.__module__ + "." + self.__class__.__name__)
        # TODO: Add sanity checks for the args
        self.host = host
        self.key = key
        self.value = value
        self.clock = clock

    def getKey(self):
        if self.key is None:
            return self.DEFAULT_KEY()
        return self.key

    def getValue(self):
        if self.value is None:
            return self.DEFAULT_VALUE()
        return self.value

    def getHost(self):
        if self.host is None:
            return self.DEFAULT_HOST()
        return self.host

    def getClock(self):
        return self.clock or time.time()

    def __repr__(self):
        if self.clock is None:
            return '%s(host=%r, key=%r, value=%r)' % (
                                                      self.__class__.__name__,
                                                      self.getHost(),
                                                      self.getKey(),
                                                      self.getValue(),
                                                      )
        return '%s(host=%r, key=%r, value=%r, clock=%r)' % (
                                                            self.__class__.__name__,
                                                            self.getHost(),
                                                            self.getKey(),
                                                            self.getValue(),
                                                            self.getClock(),
                                                            )

    def toZbxJSON(self):
        """ Convert to JSON that Zabbix will accept """
        # Zabbix has very fragile JSON parser, and we cannot use json to dump whole packet
        ret = (
               '\t\t{\n'
               '\t\t\t"host":%s,\n'
               '\t\t\t"key":%s,\n'
               '\t\t\t"value":%s,\n'
               '\t\t\t"clock":%s}'
               ) % (
                    json.dumps(self.getHost()),
                    json.dumps(self.getKey()),
                    json.dumps(self.getValue()),
                    self.getClock(),
                    )
        self.l.log(3, "Serialized %r to %r", self, ret)
        return ret
