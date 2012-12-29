from dbp.manager import TXManager
from paxos.test import TestCase
from twisted.python import failure
from twisted.internet.task import Clock


class TestManager(TestCase):

    def test_wait_on_tx_received(self):

        c = Clock()
        m = TXManager(txs=[(1, "a = b")], clock=c)

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
        d = n._reserve_tx(3)
        d.addCallback(self.gen_cb(3))
        return d

    def test_reserve_tx_recieved(self):
        # assert we fail if we've already recieved the TX we try to reserve
        l = [(1, "a = b"), (2, "b = c")]
        n = TXManager(l)
        d = n._reserve_tx(2)
        d.addBoth(self.gen_cbs())
        return d

    def test_reserve_tx_distributed(self):
        # assert we fail if we've already distributed the TX we try to reserve
        l = [(1, "a = b"), (2, "b = c")]
        n = TXManager(l)
        n.distribute(3, "a = c")
        d = n._reserve_tx(3)
        d.addBoth(self.gen_cbs())
        return d
