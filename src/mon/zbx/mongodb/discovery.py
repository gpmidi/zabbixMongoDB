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
import pymongo

# Ours
from mon.zbx.comm.metrics import DiscoveryMetric


# TODO: Add support for node and sharding discovery


class MongoDBDatabaseDiscoveryMetric(DiscoveryMetric):
    """ Discover a list of all DBs
    @note: Only provides DB names - Lowest overhead, least information provided
    """
    DEFAULT_KEY = "mongodb.server.discovery.databases"
    DEFAULT_VALUE = json.dumps(dict(data = []))

    def __init__(self, mongoClient = None, mongodHost = None, mongodPort = None):
        if mongoClient:
            self.mongoClient = mongoClient
        else:
            self.mongoClient = pymongo.MongoClient(mongodHost, mongodPort)

        # Get a list of all DB names
        self.update()


    def update(self):
        self.l.debug("Going to update DB list")
        self.dbNames = []
        self.clearMetrics()
        for db in self.mongoClient.database_names().values():
            self.l.debug("Working on db %r", db)
            self.dbNames.append(str(db))
            self.addMetric({
                            '{#DBNAME}':str(db),
                            })


class MongoDBCollectionsDBDiscoveryMetric(DiscoveryMetric):
    """ Discover a list of all collections within all DBs
    @note: Only provides DB names and collection names - Lowest overhead, least information provided
    """
    DEFAULT_KEY = "mongodb.server.discovery.databaseCollections"
    DEFAULT_VALUE = json.dumps(dict(data = []))

    def __init__(self, mongoClient = None, mongodHost = None, mongodPort = None):
        if mongoClient:
            self.mongoClient = mongoClient
        else:
            self.mongoClient = pymongo.MongoClient(mongodHost, mongodPort)
            
        if not self.mongoClient.admin.command('ping'):
            raise RuntimeError("Not connected or can't ping mongoDB")
        
        # Get a list of all DB names
        self.update()


    def update(self):
        self.l.debug("Going to update DB list")
        
        if not self.mongoClient.admin.command('ping'):
            raise RuntimeError("Not connected or can't ping mongoDB")
        
        self.dbNames = []
        self.clearMetrics()
        for dbName in self.mongoClient.database_names().values():
            self.l.debug("Working on db %r", dbName)
            self.dbNames.append(str(dbName))
            db=self.mongoClient[dbName]
            for collection in db.getCollectionNames().values():
                self.addMetric({
                                '{#DBNAME}':str(dbName),
                                '{#COLLECTION}':str(collection),
                                '{#NAMESPACE}':"%s.%s" % (dbName, collection),
                                })
