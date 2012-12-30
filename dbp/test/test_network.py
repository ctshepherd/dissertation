from dbp.network import TXNetwork
from dbp.test import TestCase


class TestTXNetwork(TestCase):
    skip = True
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
