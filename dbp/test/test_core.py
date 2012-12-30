from dbp.core import DBP
from dbp.manager import TXManager
from dbp.test import TestCase
from twisted.internet.task import Clock


class FakeNetwork(object):
    """Fake network object."""
    def __init__(self, parent=None):
        self.parent = parent
        self.distributed_txs = []

    def distribute(self, tx_id, op):
        self.distributed_txs.append((tx_id, op))


class TestDBP(TestCase):

    def test_sync_db(self):
        p = DBP()
        self.addCleanup(p.manager.txn.sock.transport.stopConnecting)
        p.manager.txn = FakeNetwork()

        p._queue((1, "a = b"))
        self.assertEqual(p.db._db, {})
        p.sync_db()
        self.assertEqual(p.db._db, {'a': 'b'})

        p._queue((2, "b = a"))
        p._queue((3, "a = a"))
        self.assertEqual(p.db._db, {'a': 'b'})
        p.sync_db()
        self.assertEqual(p.db._db, {'a': 'a', 'b': 'a'})

    def test_process(self):
        p = DBP()
        self.addCleanup(p.manager.txn.sock.transport.stopConnecting)
        p.manager.txn = FakeNetwork()

        p.process(1, "a = b")
        self.assertEqual(p.db._db, {'a': 'b'})
        self.assertRaises(ValueError, p.process, 2, "foobar")
        self.assertRaises(AssertionError, p.process, 1, "a = b")
        self.assertRaises(AssertionError, p.process, 3, "a = b")

    def test_execute(self):
        c = Clock()
        p = DBP()
        self.addCleanup(p.manager.txn.sock.transport.stopConnecting)
        p.manager = TXManager(txs=[(1, "a = b"), (2, "b = c"), (3, "a = c")], clock=c)
        self.addCleanup(p.manager.txn.sock.transport.stopConnecting)
        p.manager.txn = FakeNetwork()
        results = []

        def f(r):
            results.append(r)

        p.execute("b = a").addCallback(f)
        c.advance(1)
        self.assertEqual(results, [None])
        self.assertEqual(p.db._db, {"a": "c", "b": "a"})

    def test_execute2(self):
        p = DBP()
        c = Clock()
        self.addCleanup(p.manager.txn.sock.transport.stopConnecting)
        p.manager = TXManager(txs=[(1, "a = b"), (2, "b = c"), (3, "a = c")], clock=c)
        self.addCleanup(p.manager.txn.sock.transport.stopConnecting)
        p.manager.txn = FakeNetwork()

        p.execute("b = a")
        c.advance(1)
        p.execute("b = c")
        c.advance(1)
        p.sync_db()
        self.assertEqual(p.db._db, {"a": "c", "b": "c"})
