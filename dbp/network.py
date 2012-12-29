"""Network module.

Network module, mainly contains the TXNetwork class, which handles all network traffic for the DBP.
"""


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
        self.distributed_txs = []

    def distribute(self, tx_id, op):
        self.distributed_txs.append((tx_id, op))

    def pop(self):
        """Return a TX from the network."""
        return self.tx_list.pop(0)
