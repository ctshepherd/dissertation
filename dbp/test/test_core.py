from dbp.core import DBP
from dbp.network import TXNetwork
from paxos.util import cb
from paxos.test import TestCase
from twisted.internet import defer
from twisted.trial.unittest import SkipTest


class TestDBP(TestCase):

    def test_get_next_tx_id(self):
        v = 3
        p = DBP()
        p.txn.cur_tx = v
        self.assertEqual(p.get_next_tx_id(), v+1)
        self.assertEqual(p.txn.cur_tx, v+1)

    def test_distribute(self):
        o = object()
        p = DBP()
        p.distribute(0, o)
        self.assertEqual(p.txn.distributed_txs, [(0, o)])

    def test_sync_db(self):
        p = DBP()

        p.queue((1, "a = b"))
        self.assertEqual(p.db._db, {})
        p.sync_db()
        self.assertEqual(p.db._db, {'a': 'b'})

        p.queue((2, "b = a"))
        p.queue((3, "a = a"))
        self.assertEqual(p.db._db, {'a': 'b'})
        p.sync_db()
        self.assertEqual(p.db._db, {'a': 'a', 'b': 'a'})

    def test_process(self):
        p = DBP()
        p.process(1, "a = b")
        self.assertEqual(p.db._db, {'a': 'b'})
        self.assertRaises(ValueError, p.process, 2, "foobar")
        self.assertRaises(AssertionError, p.process, 1, "a = b")
        self.assertRaises(AssertionError, p.process, 3, "a = b")

    def test_wait_on_next_tx(self):
        l = [(1, "a = b"), (2, "b = c"), (3, "a = c")]
        p = DBP()
        p.txn = TXNetwork(list(l))
        d1 = p.wait_on_next_tx()
        d1.addCallback(self.assertEqual, l.pop(0))
        d2 = p.wait_on_next_tx()
        d2.addCallback(self.assertEqual, l.pop(0))
        d3 = p.wait_on_next_tx()
        d3.addCallback(self.assertEqual, l.pop(0))
        d = defer.DeferredList([d1, d2, d3])

        return d

    def test_wait_on_txs1(self):
        ret = []

        p = DBP()
        p.txn = TXNetwork([(1, "a = b"), (2, "b = c"), (3, "a = c")])

        # d = p.wait_on_txs(2)
        # d.addCallback(cb(p.sync_db))
        # d.addCallback(cb(self.assertEqual, (p.db._db, {"a": "b"})))
        # ret.append(d)

        # d = p.wait_on_txs(3)
        # d.addCallback(cb(p.sync_db))
        # d.addCallback(cb(self.assertEqual, (p.db._db, {"a": "b", "b": "c"})))
        # ret.append(d)

        d = p.wait_on_txs(4)
        d.addCallback(cb(p.sync_db))
        d.addCallback(cb(self.assertEqual, (p.db._db, {"a": "c", "b": "c"})))
        ret.append(d)

        return defer.DeferredList(ret)

    def test_wait_on_txs_pause(self):
        raise SkipTest("This hangs trial at the moment.")
        ret = []

        p = DBP()
        p.txn = TXNetwork([(1, "a = b"), (3, "a = c"), (2, "b = c")])

        d = p.wait_on_txs(3)
        def cb(r):
            print "called!"
            raise RuntimeError()
        #d.addCallback(cb)
        ret.append(d)

        d = p.wait_on_txs(4)
        d.addCallback(cb)
        ret.append(d)

        return defer.DeferredList(ret)

    def test_wait_on_txs2(self):
        # check the same thing happens even if TXs arrive out of order

        ret = []

        p = DBP()
        p.txn = TXNetwork([(1, "a = b"), (3, "a = c"), (2, "b = c")])

        d = p.wait_on_txs(2)
        d.addCallback(cb(p.sync_db))
        #d.addCallback(cb(self.assertEqual, (p.db._db, {"a": "c", "b": "c"})))
        ret.append(d)

        d = p.wait_on_txs(3)
        d.addCallback(cb(p.sync_db))
        # Because we've already received TX 3 it will be processed here
        #d.addCallback(cb(self.assertEqual, (p.db._db, {"a": "b", "b": "c"})))
        ret.append(d)

        d = p.wait_on_txs(4)
        d.addCallback(cb(p.sync_db))
        d.addCallback(cb(self.assertEqual, (p.db._db, {"a": "c", "b": "c"})))
        ret.append(d)

        return defer.DeferredList(ret)

    def test_wait_on_txs3(self):
        ret = []

        p = DBP()
        p.txn = TXNetwork([(1, "a = b"), (3, "a = e"), (2, "a = d")])

        d = p.wait_on_txs(2)
        d.addCallback(cb(p.sync_db))
        #d.addCallback(cb(self.assertEqual, (p.db._db, {"a": "b"})))
        ret.append(d)

        d = p.wait_on_txs(3)
        d.addCallback(cb(p.sync_db))
        # Because we've already received TX 3 it will be processed here
        # d.addCallback(cb(self.assertEqual, (p.db._db, {"a": "e"})))
        ret.append(d)

        d = p.wait_on_txs(4)
        d.addCallback(cb(p.sync_db))
        d.addCallback(cb(self.assertEqual, (p.db._db, {"a": "e"})))
        ret.append(d)

        return defer.DeferredList(ret)

    def test_execute(self):
        p = DBP()
        p.txn = TXNetwork([(1, "a = b"), (2, "b = c"), (3, "a = c")])
        d = p.execute("b = a")
        d.addCallback(cb(self.assertEqual, (p.db._db, {"a": "c", "b": "a"})))

        return d