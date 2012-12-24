"""DB module.

This module contains the DB class, the backing store for all our operations. At
the moment it only supports get and set operations but will support more later.
"""

from paxos.util import dbprint


class DB(object):
    """Database backing store class"""
    def __init__(self):
        self._db = {}

    def set(self, key, val):
        """Set a key in the database to equal val."""
        dbprint("setting %s to %s" % (key, val), level=1)
        self._db[key] = val

    def get(self, key):
        """Return the value of key in the database. Raises a KeyError if key does not exist."""
        dbprint("getting key %s" % key, level=1)
        return self._db[key]
