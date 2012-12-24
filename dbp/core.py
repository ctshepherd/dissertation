from dbp.db import DB
from dbp.network import TXNetwork, TXTaken, TXFailed
from paxos.util import cb, dbprint
from twisted.internet import defer, reactor


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
            ret.append((self.min_tx+1, self.received_txs.pop(self.min_tx+1)))
            self.min_tx += 1
        return ret


class DBP(object):
    """Main DBP object - coordinates the database."""
    def __init__(self):
        self._process_txs = []
        self.db = DB()
        self.windower = TXWindower()
        self.txn = TXNetwork()
        self.waiting_ds = {}
        self.tx_version = 0

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
        # XXX: this reads from/writes to the network
        self.txn.cur_tx += 1
        return self.txn.cur_tx

    def distribute(self, tx_id, op):
        """Distribute transaction to other nodes."""
        self.txn.distribute(tx_id, op)

    def sync_db(self):
        """Process all unprocessed TXs. Return the TX the database is at now.

        Sync our local database up to all the TXs we have received so far.
        """
        for tx in self._process_txs:
            tx_id, tx_op = tx
            self.process(tx_id, tx_op)
        self._process_txs = []

    def process(self, tx_id, s):
        """Perform the operation s with transaction id tx_id."""
        dbprint("processing op %r, tx id %d" % (s, tx_id), level=2)
        assert tx_id == self.tx_version+1, "process: tx_id %d != tx_version+1: %d" % (tx_id, self.tx_version+1)
        k, v = s.split('=')
        k = k.strip(' ')
        v = v.strip(' ')
        self.db.set(k, v)
        # This will change in the future, eg, if we allowed reads then they
        # wouldn't need to be distributed
        self.distribute(tx_id, (k, v))
        self.tx_version = tx_id

    def wait_on_next_tx(self):
        """Wait for the next TX received and return it."""
        # XXX: this reads from the network
        tx = self.txn.pop()
        d = defer.Deferred()
        reactor.callLater(0.1, d.callback, tx)
        return d

    def wait_on_txs(self, tx_id):
        """Wait until we have received all txs < tx_id.

        We can receive transactions out of order, so we want to ensure that we
        have a consistent database to work with. We keep a record of
        transactions that we've received but can't process yet in self._received_txs.
        When we have received the prior message, we pop the message off and
        process it. When self._received_txs is empty then we can return.
        """
        wait_tx = tx_id - 1
        # print "Was called waiting for tx %d" % tx_id
        # print self.waiting_ds
        dbprint("waiting on tx %d (mix tx is %d)" % (tx_id, self.windower.min_tx), level=3)
        # This loop doesn't take into account missing/timedout txs yet
        if tx_id in self.waiting_ds:
            return self.waiting_ds[tx_id]
        if self.windower.min_tx < wait_tx:
            ret = defer.Deferred()
            nearly = self.wait_on_txs(wait_tx)
            def g(result):
                tx_arrives = self.wait_on_next_tx()
                # print "wait_on_txs: g: was waiting on tx_id-1 (%d), that returned so g was fired" % (wait_tx,)
                def f(next_tx):
                    # print "wait_on_txs: g: f: was waiting on a new tx (%d) which appeared so f was fired" % (wait_tx,)
                    next_tx_id, next_tx_op = next_tx
                    self.windower.insert_tx(next_tx_id, next_tx_op)
                    self.queue_multiple(self.windower.pop_valid_txs())
                    ret.callback(None)
                tx_arrives.addCallback(f)
            nearly.addCallback(g)
            self.waiting_ds[tx_id] = ret
            def cleanup(r):
                # print "Cleaning up deferred for tx %d" % tx_id
                del self.waiting_ds[tx_id]
            ret.addCallback(cleanup)
            return ret
        else:
            # print "wait_on_txs: was waiting on %d but %d < %d so return early" % (tx_id, self.windower.min_tx, wait_tx)
            d = defer.succeed(None)
            return d

    def _get_tx(self, attempts=-1):
        """Get a TX id that this node owns.

        Return a Deferred that calls back with an asserted tx or gives up after trying attempts times, errback'ing with TXFailed.
        """
        ret = defer.Deferred()
        tx_id = self.get_next_tx_id()
        d = self.txn.assert_tx(tx_id)
        def retry(err):
            if err.check(TXTaken):
                # If we ran out of attempts, fail
                if attempts == 0:
                    ret.errback(TXFailed())
                # If we are checking the number of attempts, decrement
                if attempts > 0:
                    attempts -= 1
                # Try again
                return self._get_tx(attempts)
            return err
        d.addCallbacks(ret.callback, retry)
        return ret

    def execute(self, s, attempts=-1):
        """Execute statement s, giving up after attempts tries.

        Return a Deferred that fires when a statement is executed. Errbacks with TXFailed if we exceed attempts tries.
        """
        l = [0]
        d = self._get_tx(attempts)
        # We need to store tx_id because wait_on_txs and sync_db don't pass it
        # on
        def store_tx(tx_id):
            l[0] = tx_id
            return tx_id
        d.addCallback(store_tx)
        d.addCallback(self.wait_on_txs)
        d.addCallback(cb(self.sync_db))
        def restore_tx(ret):
            return l[0]
        d.addCallback(restore_tx)
        d.addCallback(lambda t: self.process(t, s))
        return d
