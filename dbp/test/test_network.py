from dbp.network import TXNetwork
from paxos.test import TestCase


class TestTXNetwork(TestCase):
    def test_distribute(self):
        d = TXNetwork()
        d.distribute(0, ("a", "b"))
        self.assertEqual(d.distributed_txs, [(0, ("a", "b"))])

        d = TXNetwork()
        o = object()
        d.distribute(0, o)
        self.assertEqual(d.distributed_txs, [(0, o)])
