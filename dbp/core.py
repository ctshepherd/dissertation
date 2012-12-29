from dbp.db import DB
from dbp.manager import TXManager
from paxos.util import cb, dbprint


class DBP(object):
    """Main DBP object - coordinates the database."""
    def __init__(self):
        self._process_txs = []
        self.db = DB()
        self.manager = TXManager()
        self.tx_version = 0

    def _queue(self, tx):
        """Queue a TX for processing."""
        self._process_txs.append(tx)

    def _queue_multiple(self, txs):
        """Queue a list of TXs for processing."""
        self._process_txs.extend(txs)

    def sync_db(self):
        """Process all unprocessed TXs. Return the TX the database is at now.

        Sync our local database up to all the TXs we have received so far.
        """
        dbprint("sync_db: %s" % ','.join(str(t) for t in self._process_txs), level=1)
        for tx in self._process_txs:
            tx_id, tx_op = tx
            self.process(tx_id, tx_op, distribute=False)
        self._process_txs = []

    def process(self, tx_id, s, distribute=True):
        """Perform the operation s with transaction id tx_id."""
        dbprint("processing op %r, tx id %d" % (s, tx_id), level=2)
        assert tx_id == self.tx_version+1, "process: tx_id %d != tx_version+1: %d" % (tx_id, self.tx_version+1)
        k, v = s.split('=')
        k = k.strip(' ')
        v = v.strip(' ')
        self.db.set(k, v)
        # This will change in the future, eg, if we allowed reads then they
        # wouldn't need to be distributed
        if distribute:
            self.manager.distribute(tx_id, (k, v))
        self.tx_version = tx_id

    def _load_txs(self, tx_id):
        """Helper method for execute."""
        d = self.manager.wait_on_tx(tx_id-1)
        d.addCallback(lambda r: self._queue_multiple(self.manager._store.get_txs_since(self.tx_version)))
        d.addCallback(cb(self.sync_db))
        d.addCallback(lambda r: dbprint("_load_txs(after sync_db): tx_id: %d" % tx_id, level=1))
        d.addCallback(lambda r: tx_id)
        return d

    def execute(self, s, attempts=-1):
        """Execute statement s, giving up after attempts tries.

        Return a Deferred that fires when a statement is executed. Errbacks
        with TXFailed if we exceed attempts tries.
        """
        d = self.manager.get_tx(attempts)
        d.addCallback(self._load_txs)
        d.addCallback(lambda t: self.process(t, s))
        return d
