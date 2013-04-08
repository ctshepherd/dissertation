from dbp.db import DB, parse_op, InvalidOp
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

    def process_op(self, d):
        try:
            op = parse_op(d)
            op.perform_op(self.db)
        except InvalidOp, e:
            dbprint("Invalid op (%s)" % e)

    def process_lock(self, d):
        """Handle someone requesting to take the global lock"""
        guid = d['uid']
        dbprint("lock: taken by %s" % guid, level=3)
        self.lock_holder = guid

    def process_unlock(self, d):
        """Handle someone requesting to take the global lock"""
        guid = d['uid']
        dbprint("unlock: released by %s" % guid, level=3)
        self.lock_holder = None

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
                return
            if attempts > 0:
                a = attempts - 1
            else:
                a = attempts
            self.wait(tx_id+1).addCallback(lambda r:
                self.take_lock(restart, a).addCallback(d.callback))

        op_d = self.execute({"type": "attemptlock"})
        op_d.addCallback(wait_for).addCallback(check_and_retry)
        return d

    def release_lock(self):
        return self.execute({"type": "unlock"})

    def process(self, tx_id, d):
        """Process an operation that's been passed up through Paxos."""
        dbprint("processing op %r, tx id %d" % (d, tx_id), level=4)
        assert tx_id == self.tx_version+1, "process: tx_id %d != tx_version+1: %d" % (tx_id, self.tx_version+1)
        self.history.append((tx_id, d))
        assert isinstance(d, dict), "process: %s is not a dict" % (d,)

        if self.lock_holder is not None:
            if self.lock_holder != d['uid']:
                dbprint("ignoring op '%s', lock held by %s" % (d, self.lock_holder), level=3)
                self.tx_version = tx_id
                return

        op = d['type']
        if op == "nop":
            pass
        elif op == "attemptlock":
            self.process_lock(d)
        elif op == "unlock":
            self.process_unlock(d)
        elif op == "db_op":
            self.process_op(d)
        if tx_id in self.waiters:
            for d in self.waiters[tx_id]:
                d.callback(tx_id)
            del self.waiters[tx_id]
        self.tx_version = tx_id

    def execute(self, d):
        """Execute op d, by passing down to Paxos.

        Return a Deferred that fires when a statement is executed.
        """
        d.setdefault("uid", self.uid)
        return self.manager.execute(d)
