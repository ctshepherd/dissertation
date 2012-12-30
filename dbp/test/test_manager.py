from dbp.manager import TXManager
from dbp.test import TestCase
from twisted.python import failure
from twisted.internet.task import Clock
from twisted.trial.unittest import SkipTest


class FakeNetwork(object):
    """Fake network object."""
    def __init__(self, parent=None):
        self.parent = parent
        self.distributed_txs = []

    def distribute(self, tx_id, op):
        self.distributed_txs.append((tx_id, op))


class TestManager(TestCase):

    def test_get_tx(self):
        c = Clock()
        m = TXManager(txs=[(1, "a = b")], clock=c)
        self.addCleanup(m.txn.sock.transport.stopConnecting)
        m.txn = FakeNetwork()

        results = []

        def f(r):
            results.append(r)

        d = m.get_tx()
        d.addCallback(f)
        c.advance(1)
        self.assertEqual(results, [2])

    def test_get_tx_retry(self):
        raise SkipTest("this doesn't work with the current code mockup")
        c = Clock()
        m = TXManager(txs=[(1, "a = b")], clock=c)
        self.addCleanup(m.txn.sock.transport.stopConnecting)
        m.txn = FakeNetwork()

        results = []

        def f(r):
            results.append(r)

        d = m.get_tx()
        d.addCallback(f)
        m.distribute(2, "b = c")
        c.advance(1)
        self.assertEqual(results, [3])

    def test_wait_on_tx_received(self):

        c = Clock()
        m = TXManager(txs=[(1, "a = b")], clock=c)
        self.addCleanup(m.txn.sock.transport.stopConnecting)
        m.txn = FakeNetwork()

        run_count = [0]

        def f(r):
            run_count[0] += 1

        d = m.wait_on_tx(1)
        d.addCallback(f)
        c.advance(1)
        self.assertEqual(run_count[0], 1)

    def test_wait_on_tx_distribute(self):

        c = Clock()
        m = TXManager(clock=c)
        self.addCleanup(m.txn.sock.transport.stopConnecting)
        m.txn = FakeNetwork()

        run_count = [0]

        def f(r):
            run_count[0] += 1

        d = m.wait_on_tx(1)
        d.addCallback(f)
        m.distribute(1, "a = b")
        c.advance(1)
        self.assertEqual(run_count[0], 1)


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
        l = [(1, "a = b"), (2, "b = c")]
        n = TXManager(l)
        n.txn.sock.transport.stopConnecting()
        n.txn = FakeNetwork()

        d = n._reserve_tx(3)
        d.addCallback(self.gen_cb(3))
        return d

    def test_reserve_tx_recieved(self):
        # assert we fail if we've already recieved the TX we try to reserve
        l = [(1, "a = b"), (2, "b = c")]
        n = TXManager(l)
        n.txn.sock.transport.stopConnecting()
        n.txn = FakeNetwork()

        d = n._reserve_tx(2)
        d.addBoth(self.gen_cbs())
        return d

    def test_reserve_tx_distributed(self):
        # assert we fail if we've already distributed the TX we try to reserve
        l = [(1, "a = b"), (2, "b = c")]
        n = TXManager(l)
        n.txn.sock.transport.stopConnecting()
        n.txn = FakeNetwork()

        n.distribute(3, "a = c")
        d = n._reserve_tx(3)
        d.addBoth(self.gen_cbs())
        return d
