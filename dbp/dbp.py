from paxos.util import dbprint

fake_tx_list = []
distributed_txs = []
cur_tx = 0


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


class DBP(object):
    def __init__(self):
        self._min_tx = 0
        self._received_txs = {}
        self._max_tx = 0
        self._txs = {}
        self._process_txs = []
        self.db = DB()

    def queue(self, tx):
        """Queue a TX for processing."""
        self._process_txs.append(tx)

    def get_next_tx_id(self):
        global cur_tx
        cur_tx += 1
        return cur_tx

    def distribute(self, (k, v)):
        """Distribute transaction to other nodes."""
        # This is just a stub at the moment, eventually will hand off
        # transaction to a network object that will do the dirty.
        distributed_txs.append((k, v))

    def sync_db(self):
        """Process all unprocessed TXs"""
        for t in self._process_txs:
            self.process(t)
        self._process_txs = []

    def process(self, s):
        """Actually process the transaction"""
        dbprint("processing tx %r" % s, level=2)
        k, v = s.split('=')
        k = k.strip(' ')
        v = v.strip(' ')
        self.db.set(k, v)
        # This will change in the future, eg, if we allowed reads then they
        # wouldn't need to be distributed
        self.distribute((k, v))

    def wait_on_next_tx(self):
        """Wait for the next TX and return the id"""
        # We have a fake TX list for the moment
        return fake_tx_list.pop(0)

    def wait_on_txs(self, tx_id):
        """Wait until we have received all txs < tx_id.

        We can receive transactions out of order, so we want to ensure that we
        have a consistent database to work with. We keep a record of
        transactions that we've received but can't process yet in self._received_txs.
        When we have received the prior message, we pop the message off and
        process it. When self._received_txs is empty then we can return.
        """
        wait_tx = tx_id - 1
        dbprint("waiting on tx %d (mix tx is %d)" % (tx_id, self._min_tx), level=3)
        # This loop doesn't take into account missing/timedout txs yet
        while self._min_tx < wait_tx:
            next_tx = self.wait_on_next_tx()
            next_tx_id, next_tx_op = next_tx
            dbprint("next tx is %d (%d)" % (next_tx_id, self._min_tx), level=2)
            if next_tx_id == self._min_tx+1:
                self._min_tx += 1
                while (self._min_tx+1) in self._received_txs:
                    self._process_txs.append(self._received_txs.pop(self._min_tx+1))
                    self._min_tx += 1
                self._process_txs.append(next_tx_op)
            else:
                self._received_txs[next_tx_id] = next_tx_op
        assert(not self._received_txs)

    def execute(self, s):
        tx_id = self.get_next_tx_id()
        self.wait_on_txs(tx_id)
        self.sync_db()
        self.process(s)
