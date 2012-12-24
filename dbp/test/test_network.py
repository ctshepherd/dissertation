from dbp.network import TXNetwork
from paxos.test import TestCase
from twisted.python import failure


class TestTXNetwork(TestCase):
    def test_distribute(self):
        n = TXNetwork()
        n.distribute(0, ("a", "b"))
        self.assertEqual(n.distributed_txs, [(0, ("a", "b"))])

        n = TXNetwork()
        o = object()
        n.distribute(0, o)
        self.assertEqual(n.distributed_txs, [(0, o)])

    def test_pop(self):
        l = [(0, "a = b"), (1, "b = c")]
        n = TXNetwork(l)
        self.assertEqual(n.pop(), l.pop(0))
        self.assertEqual(n.pop(), l.pop(0))

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

    def test_assert_tx_succeeds(self):
        l = [(0, "a = b"), (1, "b = c")]
        n = TXNetwork(l)
        d = n.assert_tx(2)
        d.addCallback(self.gen_cb(2))
        return d

    def test_assert_tx_recieved(self):
        # assert we fail if we've already recieved the TX we try to assert
        l = [(0, "a = b"), (1, "b = c")]
        n = TXNetwork(l)
        d = n.assert_tx(1)
        d.addBoth(self.gen_cbs())
        return d

    def test_assert_tx_distributed(self):
        # assert we fail if we've already distributed the TX we try to assert
        l = [(0, "a = b"), (1, "b = c")]
        n = TXNetwork(l)
        n.distribute(2, "a = c")
        d = n.assert_tx(2)
        d.addBoth(self.gen_cbs())
        return d
