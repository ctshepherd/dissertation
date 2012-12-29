from dbp.manager import TXManager
from dbp.network import TXNetwork
from paxos.util import cb
from paxos.test import TestCase
from twisted.python import failure
from twisted.internet import defer
from twisted.trial.unittest import SkipTest


class TestManager(TestCase):

    # def test_wait_on_next_tx(self):
    #     l = [(1, "a = b"), (2, "b = c"), (3, "a = c")]
    #     p = TXManager()
    #     p.txn = TXNetwork(list(l))
    #     d1 = p.wait_on_next_tx()
    #     d1.addCallback(self.assertEqual, l.pop(0))
    #     d2 = p.wait_on_next_tx()
    #     d2.addCallback(self.assertEqual, l.pop(0))
    #     d3 = p.wait_on_next_tx()
    #     d3.addCallback(self.assertEqual, l.pop(0))
    #     d = defer.DeferredList([d1, d2, d3])

    #     return d

    def test_wait_on_tx1(self):
        ret = []

        p = TXManager()
        p.txn = TXNetwork([(1, "a = b"), (2, "b = c"), (3, "a = c")])

        # d = p.wait_on_tx(2)
        # d.addCallback(cb(p.sync_db))
        # d.addCallback(cb(self.assertEqual, (p.db._db, {"a": "b"})))
        # ret.append(d)

        # d = p.wait_on_tx(3)
        # d.addCallback(cb(p.sync_db))
        # d.addCallback(cb(self.assertEqual, (p.db._db, {"a": "b", "b": "c"})))
        # ret.append(d)

        d = p.wait_on_tx(4)
        # d.addCallback(cb(p.sync_db))
        d.addCallback(cb(self.assertEqual, (p.db._db, {"a": "c", "b": "c"})))
        ret.append(d)

        return defer.DeferredList(ret)

    def test_wait_on_tx_pause(self):
        raise SkipTest("This hangs trial at the moment.")
        ret = []

        p = TXManager()
        p.txn = TXNetwork([(1, "a = b"), (3, "a = c"), (2, "b = c")])

        d = p.wait_on_tx(3)
        def cb(r):
            print "called!"
            raise RuntimeError()
        #d.addCallback(cb)
        ret.append(d)

        d = p.wait_on_tx(4)
        d.addCallback(cb)
        ret.append(d)

        return defer.DeferredList(ret)

    def test_wait_on_tx2(self):
        # check the same thing happens even if TXs arrive out of order

        ret = []

        p = TXManager()
        p.txn = TXNetwork([(1, "a = b"), (3, "a = c"), (2, "b = c")])

        d = p.wait_on_tx(2)
        # d.addCallback(cb(p.sync_db))
        #d.addCallback(cb(self.assertEqual, (p.db._db, {"a": "c", "b": "c"})))
        ret.append(d)

        d = p.wait_on_tx(3)
        # d.addCallback(cb(p.sync_db))
        # Because we've already received TX 3 it will be processed here
        #d.addCallback(cb(self.assertEqual, (p.db._db, {"a": "b", "b": "c"})))
        ret.append(d)

        d = p.wait_on_tx(4)
        # d.addCallback(cb(p.sync_db))
        d.addCallback(cb(self.assertEqual, (p.db._db, {"a": "c", "b": "c"})))
        ret.append(d)

        return defer.DeferredList(ret)

    def test_wait_on_tx3(self):
        ret = []

        p = TXManager()
        p.txn = TXNetwork([(1, "a = b"), (3, "a = e"), (2, "a = d")])

        d = p.wait_on_tx(2)
        # d.addCallback(cb(p.sync_db))
        #d.addCallback(cb(self.assertEqual, (p.db._db, {"a": "b"})))
        ret.append(d)

        d = p.wait_on_tx(3)
        # d.addCallback(cb(p.sync_db))
        # Because we've already received TX 3 it will be processed here
        # d.addCallback(cb(self.assertEqual, (p.db._db, {"a": "e"})))
        ret.append(d)

        d = p.wait_on_tx(4)
        # d.addCallback(cb(p.sync_db))
        d.addCallback(cb(self.assertEqual, (p.db._db, {"a": "e"})))
        ret.append(d)

        return defer.DeferredList(ret)

class TestReserveTX(TestCase):
    def gen_cbs(self):
        """Return a function that asserts it is called with a failure"""
        def f(result):
            self.assertIsInstance(result, failure.Failure)
        return f

    def gen_cb(self, x):
        """Return a function that asserts it is called with x"""
        def f(result):
            self.assertEqual(result, x)
        return f

    def test_reserve_tx_succeeds(self):
        l = [(0, "a = b"), (1, "b = c")]
        n = TXManager(l)
        d = n._reserve_tx(2)
        d.addCallback(self.gen_cb(2))
        return d

    def test_reserve_tx_recieved(self):
        # assert we fail if we've already recieved the TX we try to reserve
        l = [(0, "a = b"), (1, "b = c")]
        n = TXManager(l)
        d = n._reserve_tx(1)
        d.addBoth(self.gen_cbs())
        return d

    def test_reserve_tx_distributed(self):
        # assert we fail if we've already distributed the TX we try to reserve
        l = [(0, "a = b"), (1, "b = c")]
        n = TXManager(l)
        n.distribute(2, "a = c")
        d = n._reserve_tx(2)
        d.addBoth(self.gen_cbs())
        return d
