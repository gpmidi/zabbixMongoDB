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
import csv

try:
    # Python 3.x?
    import json  # @UnresolvedImport
except:
    # Python 2.7
    import simplejson as json  # @UnresolvedImport @Reimport

# Others

# Ours
from mon.zbx.comm.metrics import DiscoveryMetric


# TODO: Add support for node and sharding discovery


class WWWDiscoveryMetric(DiscoveryMetric):
    """ Discover a list of all domains
    """
    DEFAULT_KEY = "www.domains"
    DEFAULT_VALUE = json.dumps(dict(data = []))

    def __init__(self, domainsCSV):

        self.domainsCSV = domainsCSV

        # Get a list of all DB names
        self.update()


    def update(self):
        self.l.debug("Going to update domains list")

        self.clearMetrics()
        with open(self.domainsCSV, 'rb') as f:
            for line in csv.DictReader(f):
                name = line['DomainName'].lower()
                self.l.debug("Working on domain %r", name)
                self.dbNames.append(str(name))
                self.addMetric({
                            '{#DOMAIN}':str(name),
                            })

