"""Contains TXWindower class."""

from dbp.network import TXNetwork, TXTaken, TXFailed
from dbp.util import dbprint
from twisted.python import failure
from twisted.internet import defer, reactor


class TXStore(object):
    """Maintains a moving "window" of received transactions.

    In order to ensure we process received transactions in order, we maintain a
    window and fill in "holes" when we eventually receive those transactions.
    """
    def __init__(self):
        self.received_txs = {}
        self._max_valid_tx = 0

    def insert_tx(self, tx_id, tx_op):
        """Insert a transaction.

        Insert a transaction into the datastructure and potentially update _max_valid_tx.
        """
        self.received_txs[tx_id] = tx_op
        while (self._max_valid_tx+1) in self.received_txs:
            self._max_valid_tx += 1

    def __contains__(self, tx_id):
        return tx_id <= self._max_valid_tx

    def __getitem__(self, tx_id):
        return self.received_txs[tx_id]

    def get_txs_since(self, tx_id):
        return [(x, self.received_txs[x]) for x in xrange(tx_id+1, self._max_valid_tx+1)]


class TXManager(object):
    def __init__(self, txs=(), clock=None):
        self._store = TXStore()
        self._waiters = {}
        self.txn = TXNetwork()
        self.cur_tx = 0
        if clock is None:
            clock = reactor
        self.clock = clock
        self._taken_txs = set()
        for tx_id, op in txs:
            self._taken_txs.add(tx_id)
            self._receive_tx(tx_id, op)

    def _get_next_tx_id(self):
        """Return the next (potentially) viable TX across the whole network.

        This returns a TX id which we are guessing is a valid TX to use for our
        operation. If we pick one too far on we will have to wait for previous
        transactions to be issued before we can execute, if we pick one too
        close we will be beaten to issueing that TX by another node. The code
        doesn't go into those complexities at this point but it will do soon,
        for now we use a global counter.
        """
        return self.cur_tx + 1

    def distribute(self, tx_id, op):
        """Distribute transaction to other nodes."""
        self._receive_tx(tx_id, op)
        self.txn.distribute(tx_id, op)

    def _receive_tx(self, tx_id, op):
        # Similar to assert in DPB.process
        assert tx_id == self.cur_tx+1, "_receive: tx_id %d != cur_tx+1: %d" % (tx_id, self.cur_tx+1)
        dbprint("_receive_tx: tx_id: %s, op: %s" % (tx_id, op), level=1)
        # XXX: Should we do some kind of error checking here? (try/except etc)
        self._taken_txs.add(tx_id)
        self._store.insert_tx(tx_id, op)
        self._notify_waiters(tx_id)
        self.cur_tx += 1

    def _notify_waiters(self, tx_id):
        dbprint("_notify_waiters: notifying waiters on tx_id: %d (%s)" % (tx_id, self._waiters), level=1)
        if tx_id in self._waiters:
            for d in self._waiters.pop(tx_id):
                d.callback(tx_id)

    def wait_on_tx(self, tx_id):
        """Wait until we have received all txs < tx_id.

        We can receive transactions out of order, so we want to ensure that we
        have a consistent database to work with. We keep a record of
        transactions that we've received but can't process yet in self._received_txs.
        When we have received the prior message, we pop the message off and
        process it. When self._received_txs is empty then we can return.
        """

        dbprint("wait_on_tx: adding waiter on tx_id: %d" % tx_id, level=1)
        if tx_id in self._store:
            ret = defer.succeed(tx_id)
        else:
            ret = defer.Deferred()
            self._waiters.setdefault(tx_id, []).append(ret)
        return ret

    def get_tx(self, attempts=-1):
        """Return a TX id reserved for this node.

        Return a Deferred that calls back with a reserved tx or gives up after trying attempts times, errback'ing with TXFailed.
        """

        ret = defer.Deferred()
        tx_id = self._get_next_tx_id()
        d = self._reserve_tx(tx_id)
        a = [attempts]

        def retry(err):
            if err.check(TXTaken):
                # If we ran out of attempts, fail
                if a[0] == 0:
                    ret.errback(TXFailed())
                # If we are checking the number of attempts, decrement
                if a[0] > 0:
                    a[0] -= 1
                # Try again
                return self.get_tx(attempts)
            return err
        d.addCallbacks(ret.callback, retry)
        return ret

    def _reserve_tx(self, tx_id):
        """Attempt to reserve TX with id tx_id for this node.

        Returns a Deferred that calls back with tx_id if we can reserve tx_id, or errback with TXTaken otherwise."""
        # This will call down to Paxos eventually
        dbprint("_reserve_tx: tx_id: %d taken_txs: %s" % (tx_id, ','.join(str(i) for i in self._taken_txs)), level=1)
        d = defer.Deferred()
        if tx_id not in self._taken_txs:
            self.clock.callLater(0.1, d.callback, tx_id)
        else:
            self.clock.callLater(0.1, d.errback, failure.Failure(TXTaken(tx_id)))
        return d
