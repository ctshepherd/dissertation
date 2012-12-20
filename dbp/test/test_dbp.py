from dbp import dbp
from dbp.dbp import DB, DBP
from paxos.test import TestCase


class TestDB(TestCase):
    def test_set(self):
        db = DB()
        db.set("foo", "bar")
        self.assertEqual(db.get("foo"), "bar")
        self.assertRaises(KeyError, db.get, "foobar")


class TestDBP(TestCase):

    def test_get_next_tx_id(self):
        v = 3
        c = dbp.cur_tx
        dbp.cur_tx = v
        p = DBP()
        self.assertEqual(p.get_next_tx_id(), v+1)
        self.assertEqual(dbp.cur_tx, v+1)
        dbp.cur_tx = c

    def test_distribute(self):
        d = dbp.distributed_txs
        dbp.distributed_txs = []

        p = DBP()
        p.distribute(("a", "b"))
        self.assertEqual(dbp.distributed_txs, [("a", "b")])

        dbp.distributed_txs = d

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
        f = dbp.fake_tx_list
        l = [(1, "a = b"), (2, "b = c"), (3, "a = c")]
        dbp.fake_tx_list = list(l)  # copy l into fake_tx_list

        p = DBP()
        self.assertEqual(p.wait_on_next_tx(), l.pop(0))
        self.assertEqual(p.wait_on_next_tx(), l.pop(0))
        self.assertEqual(p.wait_on_next_tx(), l.pop(0))

        dbp.fake_tx_list = f

    def test_wait_on_txs(self):
        f = dbp.fake_tx_list

        l = [(1, "a = b"), (2, "b = c"), (3, "a = c")]
        dbp.fake_tx_list = list(l)  # copy l into fake_tx_list

        p = DBP()
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
        dbp.fake_tx_list = list(l)  # copy l into fake_tx_list
        p = DBP()
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
        dbp.fake_tx_list = list(l)  # copy l into fake_tx_list
        p = DBP()
        p.wait_on_txs(2)
        p.sync_db()
        self.assertEqual(p.db._db, {"a": "b"})
        p.wait_on_txs(3)
        p.sync_db()
        self.assertEqual(p.db._db, {"a": "e"})
        p.wait_on_txs(4)
        p.sync_db()
        self.assertEqual(p.db._db, {"a": "e"})

        dbp.fake_tx_list = f

    def test_execute(self):
        f = dbp.fake_tx_list
        c = dbp.cur_tx
        dbp.fake_tx_list = [(1, "a = b"), (2, "b = c"), (3, "a = c")]
        dbp.cur_tx = len(dbp.fake_tx_list)

        p = DBP()
        p.execute("b = a")
        self.assertEqual(p.db._db, {"a": "c", "b": "a"})

        dbp.fake_tx_list = f
        dbp.cur_tx = c
