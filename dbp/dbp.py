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


class Distributor(object):
    """Distributes TXs across the network"""
    def __init__(self):
        pass

    def distribute(self, tx):
        # XXX: this writes to the network
        distributed_txs.append(tx)


class TXWindower(object):
    """Maintains a moving "window" of received transactions.

    In order to ensure we process received transactions in order, we maintain a
    window and fill in "holes" when we eventually receive those transactions.
    """
    def __init__(self):
        self.received_txs = {}
        self.min_tx = 0
        self.max_tx = 0

    def insert_tx(self, tx_id, tx_op):
        """Insert a transaction.

        Insert a transaction into the datastructure and potentially update max_tx.
        """
        self.received_txs[tx_id] = tx_op
        if tx_id > self.max_tx:
            self.max_tx = tx_id

    def pop_valid_txs(self):
        """Return the largest number of contiguous TXs, starting from min_tx."""
        ret = []
        while (self.min_tx+1) in self.received_txs:
            ret.append(self.received_txs.pop(self.min_tx+1))
            self.min_tx += 1
        return ret


class DBP(object):
    """Main DBP object - coordinates the database."""
    def __init__(self):
        self._process_txs = []
        self.db = DB()
        self.distributor = Distributor()
        self.windower = TXWindower()

    def queue(self, tx):
        """Queue a TX for processing."""
        self._process_txs.append(tx)

    def queue_multiple(self, txs):
        """Queue a list of TXs for processing."""
        self._process_txs.extend(txs)

    def get_next_tx_id(self):
        """Return the next (potentially) viable TX across the whole network.

        This returns a TX id which we are guessing is a valid TX to use for our
        operation. If we pick one too far on we will have to wait for previous
        transactions to be issued before we can execute, if we pick one too
        close we will be beaten to issueing that TX by another node. The code
        doesn't go into those complexities at this point but it will do soon,
        for now we use a global counter.
        """
        # XXX: this writes to the network
        global cur_tx
        cur_tx += 1
        return cur_tx

    def distribute(self, tx):
        """Distribute transaction to other nodes."""
        self.distributor.distribute(tx)

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
        """Wait for the next TX received and return it."""
        # We have a fake TX list for the moment
        # XXX: this reads from the network
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
        dbprint("waiting on tx %d (mix tx is %d)" % (tx_id, self.windower.min_tx), level=3)
        # This loop doesn't take into account missing/timedout txs yet
        while self.windower.min_tx < wait_tx:
            next_tx = self.wait_on_next_tx()
            next_tx_id, next_tx_op = next_tx
            dbprint("next tx is %d (%d)" % (next_tx_id, self.windower.min_tx), level=2)
            self.windower.insert_tx(next_tx_id, next_tx_op)
            self.queue_multiple(self.windower.pop_valid_txs())

    def execute(self, s):
        """Execute a statement."""
        tx_id = self.get_next_tx_id()
        self.wait_on_txs(tx_id)
        self.sync_db()
        self.process(s)
