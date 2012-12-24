"""Network module.

Network module, mainly contains the TXNetwork class, which handles all network traffic for the DBP.
"""

from twisted.internet import defer, reactor
from twisted.python import failure


class TXTaken(Exception):
    """Raised when we try to reserve a TX but it was taken by someone else."""


class TXFailed(Exception):
    """Raised when we have exceeded number of attempts to try to reserve a TX."""


class TXNetwork(object):
    """Fake network object. Will be replaced by something cleverer later.

    Distributes TXs across the network and returns a prepopulated list of TXs when asked.
    """
    def __init__(self, txs=()):
        self.tx_list = list(txs)
        self.cur_tx = len(txs)
        self.distributed_txs = []
        self.taken_txs = set(txi for (txi, txo) in txs)

    def distribute(self, tx_id, op):
        self.distributed_txs.append((tx_id, op))
        self.taken_txs.add(tx_id)
        self.cur_tx += 1

    def pop(self):
        """Return a TX from the network."""
        return self.tx_list.pop(0)

    def reserve_tx(self, tx_id):
        """Attempt to reserve TX with id tx_id for this node.

        Returns a Deferred that calls back with tx_id if we can reserve tx_id, or errback with TXTaken otherwise."""
        # This will call down to Paxos eventually
        d = defer.Deferred()
        if tx_id not in self.taken_txs:
            reactor.callLater(0.1, d.callback, tx_id)
        else:
            reactor.callLater(0.1, d.errback, failure.Failure(TXTaken(tx_id)))
        return d
