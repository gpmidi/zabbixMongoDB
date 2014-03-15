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


class WWWDiscoveryMetric(DiscoveryMetric):
    """ Discover a list of all domains
    """
    DEFAULT_KEY = lambda x: "discovery.domains"
    DEFAULT_VALUE = lambda metric: json.dumps(dict(data = []))

    def __init__(self, domainsCSV, **kwargs):
        super(WWWDiscoveryMetric, self).__init__(**kwargs)
        self.domainsCSV = domainsCSV

        # Get a list of all DB names
        self.update()


    def update(self):
        self.l.debug("Going to update domains list")

        self.clearMetrics()
        with open(self.domainsCSV, 'r') as f:
            for line in csv.DictReader(f):
                name = line['DomainName'].lower()
                self.l.debug("Working on domain %r", name)
                self.addMetric(**{
                            '{#DOMAIN}':str(name),
                            })

