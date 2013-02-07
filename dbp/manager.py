"""Contains TXWindower class."""

from dbp.network import DBPNode
from twisted.internet import reactor


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

    def valid(self, tx_id):
        return tx_id <= self._max_valid_tx

    def __getitem__(self, tx_id):
        return self.received_txs[tx_id]

    def get_txs_since(self, tx_id):
        return [(x, self.received_txs[x]) for x in xrange(tx_id+1, self._max_valid_tx+1)]


class TXManager(object):
    def __init__(self, dbp, port=None, bootstrap=None, txs=(), clock=None):
        self.dbp = dbp
        self._store = TXStore()
        # self._waiters = {}
        self.node = DBPNode(self, bootstrap)
        if port is None:
            port = 0
        t = reactor.listenUDP(port, self.node)
        self.cur_tx = 0

    def execute(self, op):
        return self.node.run(op)

    def _passup_tx(self, tx):
        tx_id, op = tx
        self._store.insert_tx(tx_id, op)
        # If this TX is valid, update our notion of cur_tx and notify people
        # waiting on TXs up to this one.
        if self._store.valid(tx_id):
            for ti in xrange(self.cur_tx+1, tx_id+1):
                self.dbp.process(ti, self._store[ti])
                # self._notify_waiters(ti)
            self.cur_tx = tx_id
        else:
            # otherwise try and push for ops we haven't heard about
            for ti in xrange(self.cur_tx+1, tx_id):
                if ti not in self._store.received_txs:
                    self.node.chase_up(ti)

    # def _notify_waiters(self, tx_id):
    #     dbprint("_notify_waiters: notifying waiters on tx_id: %d (%s)" % (tx_id, self._waiters), level=1)
    #     if tx_id in self._waiters:
    #         for d in self._waiters.pop(tx_id):
    #             d.callback(tx_id)

    # def wait_on_tx(self, tx_id):
    #     """Wait until we have received all txs < tx_id.

    #     We can receive transactions out of order, so we want to ensure that we
    #     have a consistent database to work with. We keep a record of
    #     transactions that we've received but can't process yet in self._received_txs.
    #     When we have received the prior message, we pop the message off and
    #     process it. When self._received_txs is empty then we can return.
    #     """

    #     dbprint("wait_on_tx: adding waiter on tx_id: %d" % tx_id, level=1)
    #     if tx_id in self._store:
    #         ret = defer.succeed(tx_id)
    #     else:
    #         ret = defer.Deferred()
    #         self._waiters.setdefault(tx_id, []).append(ret)
    #     return ret
