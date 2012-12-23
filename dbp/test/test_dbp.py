from dbp import dbp
from dbp.dbp import DB, DBP, TXNetwork
from paxos.test import TestCase


class TestDB(TestCase):
    def test_set(self):
        db = DB()
        db.set("foo", "bar")
        self.assertEqual(db.get("foo"), "bar")
        self.assertRaises(KeyError, db.get, "foobar")


class TestTXNetwork(TestCase):
    def test_distribute(self):
        d = TXNetwork()
        d.distribute(("a", "b"))
        self.assertEqual(d.distributed_txs, [("a", "b")])

        d = TXNetwork()
        o = object()
        d.distribute(o)
        self.assertEqual(d.distributed_txs, [o])


class TestDBP(TestCase):

    def test_get_next_tx_id(self):
        v = 3
        p = DBP()
        p.txn.cur_tx = v
        self.assertEqual(p.get_next_tx_id(), v+1)
        self.assertEqual(p.txn.cur_tx, v+1)

    def test_distribute(self):
        l = []
        o = object()
        p = DBP()
        p.distribute(o)
        self.assertEqual(p.txn.distributed_txs, [o])

    def test_sync_db(self):
        p = DBP()

        p.queue("a = b")
        self.assertEqual(p.db._db, {})
        p.sync_db()
        self.assertEqual(p.db._db, {'a': 'b'})

        p.queue("b = a")
        p.queue("a = a")
        self.assertEqual(p.db._db, {'a': 'b'})
        p.sync_db()
        self.assertEqual(p.db._db, {'a': 'a', 'b': 'a'})

    def test_process(self):
        p = DBP()
        p.process("a = b")
        self.assertEqual(p.db._db, {'a': 'b'})
        self.assertRaises(ValueError, p.process, "foobar")

    def test_wait_on_next_tx(self):
        l = [(1, "a = b"), (2, "b = c"), (3, "a = c")]
        p = DBP()
        p.txn = TXNetwork(list(l))
        self.assertEqual(p.wait_on_next_tx(), l.pop(0))
        self.assertEqual(p.wait_on_next_tx(), l.pop(0))
        self.assertEqual(p.wait_on_next_tx(), l.pop(0))

    def test_wait_on_txs(self):
        l = [(1, "a = b"), (2, "b = c"), (3, "a = c")]

        p = DBP()
        p.txn = TXNetwork(list(l))
        p.wait_on_txs(2)
        p.sync_db()
        self.assertEqual(p.db._db, {"a": "b"})
        p.wait_on_txs(3)
        p.sync_db()
        self.assertEqual(p.db._db, {"a": "b", "b": "c"})
        p.wait_on_txs(4)
        p.sync_db()
        self.assertEqual(p.db._db, {"a": "c", "b": "c"})

        # check the same thing happens even if TXs arrive out of order
        l = [(1, "a = b"), (3, "a = c"), (2, "b = c")]
        p = DBP()
        p.txn = TXNetwork(list(l))
        p.wait_on_txs(2)
        p.sync_db()
        self.assertEqual(p.db._db, {"a": "b"})
        p.wait_on_txs(3)
        p.sync_db()
        # Because we've already received TX 3 it will be processed here
        self.assertEqual(p.db._db, {"a": "c", "b": "c"})
        p.wait_on_txs(4)
        p.sync_db()
        self.assertEqual(p.db._db, {"a": "c", "b": "c"})

        l = [(1, "a = b"), (3, "a = e"), (2, "a = d")]
        p = DBP()
        p.txn = TXNetwork(list(l))
        p.wait_on_txs(2)
        p.sync_db()
        self.assertEqual(p.db._db, {"a": "b"})
        p.wait_on_txs(3)
        p.sync_db()
        self.assertEqual(p.db._db, {"a": "e"})
        p.wait_on_txs(4)
        p.sync_db()
        self.assertEqual(p.db._db, {"a": "e"})

    def test_execute(self):
        p = DBP()
        p.txn = TXNetwork([(1, "a = b"), (2, "b = c"), (3, "a = c")])
        p.execute("b = a")
        self.assertEqual(p.db._db, {"a": "c", "b": "a"})
