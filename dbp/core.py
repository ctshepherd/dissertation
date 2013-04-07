from dbp.db import DB
from dbp.manager import TXManager
from dbp.util import dbprint
from collections import defaultdict
from twisted.internet.defer import Deferred


class DBP(object):
    """Main DBP object - coordinates the database."""

    def __init__(self, port=None, bootstrap=None):
        self.db = DB()
        self.manager = TXManager(self, port, bootstrap)
        self.uid = self.manager.node.uid
        self.tx_version = 0
        self.lock_holder = None
        self.history = []
        self.waiters = defaultdict(list)

    def wait(self, tx_id):
        d = Deferred()
        if tx_id <= self.tx_version:
            d.callback(tx_id)
        else:
            self.waiters[tx_id].append(d)
        return d

    def process_assign(self, s):
        k, v = s.split('=')
        k = k.strip(' ')
        v = v.strip(' ')
        self.db.set(k, v)

    def process_lock(self, s):
        """Handle someone requesting to take the global lock"""
        op, guid = s.split(':', 1)
        if self.lock_holder is None:
            dbprint("lock: taken by %s" % guid, level=3)
            self.lock_holder = guid
        else:
            dbprint("lock: not taken by %s" % guid, level=3)

    def process_unlock(self, s):
        """Handle someone requesting to take the global lock"""
        op, guid = s.split(':', 1)
        if self.lock_holder == guid:
            dbprint("unlock: released by %s" % guid, level=3)
            self.lock_holder = None
        else:
            dbprint("unlock: %s tried to unlock but didn't own the lock (%s did)" % (guid, self.lock_holder), level=3)

    def owns_lock(self):
        return self.lock_holder == self.uid

    def take_lock(self, restart=True, attempts=-1):
        d = Deferred()

        def wait_for(i):
            return self.wait(i['instance_id'])

        def check_and_retry(tx_id):
            if self.owns_lock():
                d.callback(tx_id)
                return
            if attempts == 0 or not restart:
                d.errback("couldn't take lock")
            if attempts > 0:
                a = attempts - 1
            else:
                a = attempts
            self.take_lock(restart, a)

        op_d = self.execute("attemptlock:%s" % self.uid)
        op_d.addCallback(wait_for).addCallback(check_and_retry)
        return d

    def release_lock(self):
        return self.execute("unlock:%s" % self.uid)

    def process(self, tx_id, s):
        """Process an operation that's been passed up through Paxos."""
        dbprint("processing op %r, tx id %d" % (s, tx_id), level=4)
        assert tx_id == self.tx_version+1, "process: tx_id %d != tx_version+1: %d" % (tx_id, self.tx_version+1)
        self.history.append((tx_id, s))
        if s == "nop":
            pass
        elif s.startswith("attemptlock"):
            self.process_lock(s)
        elif s.startswith("unlock"):
            self.process_unlock(s)
        else:
            self.process_assign(s)
        if tx_id in self.waiters:
            for d in self.waiters[tx_id]:
                d.callback(tx_id)
            del self.waiters[tx_id]
        self.tx_version = tx_id

    def execute(self, s):
        """Execute statement s, by passing down to Paxos.

        Return a Deferred that fires when a statement is executed.
        """
        return self.manager.execute(s)
