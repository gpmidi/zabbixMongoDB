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

# Others
import pymongo

# Ours
from mon.zbx.comm.metric import Metric


class MongoDBDatabaseStatSender(object):
    def __init__(self,
                 dbName,
                 server,
                 mongoClient = None,
                 mongodHost = None,
                 mongodPort = None,
                 metricHost = None,
                 metricClock = None,
                 baseKey = "mongodb.server.db",
                 **kwargs
                 ):
        self.server = server
        self.baseKey = baseKey
        self.metricArgs = kwargs
        if metricClock is not None:
            self.metricArgs['clock']=metricClock
        if metricHost is not None:
            self.metricArgs['host']=metricHost

        if mongoClient:
            self.mongoClient = mongoClient
        else:
            self.mongoClient = pymongo.MongoClient(mongodHost, mongodPort)
        self.dbName=dbName
        self.db=self.mongoClient[self.dbName]
        
        self.update()
        
    def _flatten(self,d,lst=None,parentKs=[],seperator='.'):
        # Caution: Uses side-effects to modify lst
        if lst is None:
            lst={}
        if isinstance(d,collections.MutableMapping):
            # Dicts
            for k,v in d.items():
                indexList=parentKs+[str(k),]
                self._flatten(d=v,lst=lst,parentKs=indexList,seperator=seperator)
        elif isinstance(d,collections.MutableSequence):
            # Lists
            for index in xrange(0,len(d)):
                indexList=parentKs+[str(index),]
                self._flatten(d=d[index],lst=lst,parentKs=indexList,seperator=seperator)
        else:
            # Int/string/float/etc
            lst['.'.join(parentKs)]=d
        return lst
    
    def update(self):
        for k, v in self._flatten(d = self.db.stats()).items():
            metric = Metric(
                            key = "%s.%s[%s]" % (
                                               self.baseKey,
                                               k,
                                               self.dbName,
                                               ),
                            value = v,
                            **self.metricArgs
                            )
            self.server.queueMetric(metric = metric, priority = 10)
            
        
