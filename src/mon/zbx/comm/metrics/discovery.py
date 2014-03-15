'''
Created on Jan 12, 2014

@author: Paulson McIntyre (GpMidi) <paul@gpmidi.net>
'''
# Built-in
import time
import logging
import socket
import collections
import re

try:
    # Python 3.x?
    import json  # @UnresolvedImport
except:
    # Python 2.7
    import simplejson as json  # @UnresolvedImport @Reimport

# Others

# Ours
from mon.zbx.comm.metric import Metric


class DiscoveryMetric(Metric):
    """ Helps with low-level item/graph/etc discovery
    """
    DEFAULT_KEY = lambda metric: "discovery.default"
    DEFAULT_VALUE = lambda metric: json.dumps(dict(data = []))
    ENFORCE_METRIC_MACRO = True
    ENFORCE_METRIC_MACRO_MATCH = re.compile(r'^\{\#[A-Z0-9_\-]+\}$') 
    
    
    def __init__(self, discovered = None, value = None, **kwargs):
        self.discovered = discovered
        super(DiscoveryMetric, self).__init__(value = value, **kwargs)

    def getDiscovered(self):
        if self.discovered is None:
            self.discovered = []
        assert isinstance(self.discovered, collections.Iterable), "Expected discovered to be itterable. Got %r. " % self.discovered

        # TODO: Add handling of discovered not being itterable
        if self.ENFORCE_METRIC_MACRO:
            for discovered in self.discovered:
                assert isinstance(discovered, dict), "Expected discovered type of %r to be a dict" % discovered
                for k,v in discovered.items():
                    assert self.ENFORCE_METRIC_MACRO_MATCH.match(k), "Metric's macro name is invalid. Got %r" % k
                    assert isinstance(v, str) or isinstance(v, unicode), "Metric value %r isn't a string" % v
        return self.discovered

    def addMetric(self, **macros):
        if self.discovered is None:
            self.discovered = []
        assert len(macros)>0,"Expected at least one macro to be set. Got %r"%macros
        if self.ENFORCE_METRIC_MACRO:
            for k,v in macros.items():
                assert self.ENFORCE_METRIC_MACRO_MATCH.match(k), "Metric's macro name is invalid. Got %r" % k
                assert isinstance(v, str) or isinstance(v, unicode), "Metric value %r isn't a string" % v
        self.discovered.append(macros)

    def clearMetrics(self):
        self.discovered = []

    def getValue(self):
        asObjs = dict(data = self.getDiscovered())
        asStr = json.dumps(asObjs, indent = 0).replace('   ', '\t')\
                .replace('{\n', '\t{\n').replace('\n}, \n', '\t}\n\t,\n')\
                .replace('"{#', '\t\t"{#').replace('\n}\n', '\t}\n')\
                .replace('": "', '":"').replace('\t{\n\"data\": ', '{\n\"data\":')
        self.l.log(3, "Created JSON %r from %r", asStr, asObjs)
        return asStr

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
