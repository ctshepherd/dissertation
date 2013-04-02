from dbp.db import DB, parse_op, InvalidOp
from dbp.manager import TXManager
from dbp.util import dbprint


class DBP(object):
    """Main DBP object - coordinates the database."""

    def __init__(self, port=None, bootstrap=None):
        self.db = DB()
        self.manager = TXManager(self, port, bootstrap)
        self.uid = self.manager.node.uid
        self.tx_version = 0
        self.lock_holder = None
        self.history = []

    def process_op(self, d):
        try:
            op = parse_op(d)
        except InvalidOp, e:
            dbprint("Invalid op (%s)" % e)
        op.perform_op(self.db)

    def process_lock(self, d):
        """Handle someone requesting to take the global lock"""
        guid = d['uid']
        if self.lock_holder is None:
            dbprint("lock: taken by %s" % guid, level=3)
            self.lock_holder = guid
        else:
            dbprint("lock: not taken by %s" % guid, level=3)

    def process_unlock(self, d):
        """Handle someone requesting to take the global lock"""
        guid = d['uid']
        if self.lock_holder == guid:
            dbprint("unlock: released by %s" % guid, level=3)
            self.lock_holder = None
        else:
            dbprint("unlock: %s tried to unlock but didn't own the lock (%s did)" % (guid, self.lock_holder), level=3)

    def owns_lock(self):
        return self.lock_holder == self.uid

    def take_lock(self):
        return self.execute({"type": "attemptlock", "uid": self.uid})

    def release_lock(self):
        return self.execute({"type": "unlock", "uid": self.uid})

    def process(self, tx_id, d):
        """Process an operation that's been passed up through Paxos."""
        dbprint("processing op %r, tx id %d" % (d, tx_id), level=4)
        assert tx_id == self.tx_version+1, "process: tx_id %d != tx_version+1: %d" % (tx_id, self.tx_version+1)
        self.history.append((tx_id, d))
        assert isinstance(d, dict), "process: %s is not a dict" % (d,)
        op = d['type']
        if op == "nop":
            pass
        elif op == "attemptlock":
            self.process_lock(d)
        elif op == "unlock":
            self.process_unlock(d)
        elif op == "db_op":
            self.process_op(d)
        self.tx_version = tx_id

    def execute(self, d):
        """Execute op d, by passing down to Paxos.

        Return a Deferred that fires when a statement is executed.
        """
        return self.manager.execute(d)
