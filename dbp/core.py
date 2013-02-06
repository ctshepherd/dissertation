from dbp.db import DB
from dbp.manager import TXManager
from dbp.util import dbprint


class DBP(object):
    """Main DBP object - coordinates the database."""

    def __init__(self, port=None, bootstrap=None):
        self.db = DB()
        self.manager = TXManager(self, port, bootstrap)
        self.tx_version = 0

    def process(self, tx_id, s):
        """Process an operation that's been passed up through Paxos."""
        dbprint("processing op %r, tx id %d" % (s, tx_id), level=2)
        assert tx_id == self.tx_version+1, "process: tx_id %d != tx_version+1: %d" % (tx_id, self.tx_version+1)
        k, v = s.split('=')
        k = k.strip(' ')
        v = v.strip(' ')
        self.db.set(k, v)
        self.tx_version = tx_id

    def execute(self, s):
        """Execute statement s, by passing down to Paxos.

        Return a Deferred that fires when a statement is executed.
        """
        return self.manager.execute(s)
