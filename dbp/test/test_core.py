from dbp.core import DBP
from dbp.manager import TXManager
from dbp.test import TestCase, enable_debug
from twisted.internet.task import Clock


class TestDBP(TestCase):

    def test_sync_db(self):
        p = DBP()

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
        p.process(1, "a = b")
        self.assertEqual(p.db._db, {'a': 'b'})
        self.assertRaises(ValueError, p.process, 2, "foobar")
        self.assertRaises(AssertionError, p.process, 1, "a = b")
        self.assertRaises(AssertionError, p.process, 3, "a = b")

    def test_execute(self):
        c = Clock()
        p = DBP()
        p.manager = TXManager(txs=[(1, "a = b"), (2, "b = c"), (3, "a = c")], clock=c)
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
        p.manager = TXManager(txs=[(1, "a = b"), (2, "b = c"), (3, "a = c")], clock=c)
        d = p.execute("b = a")
        c.advance(1)
        p.execute("b = c")
        c.advance(1)
        p.sync_db()
        self.assertEqual(p.db._db, {"a": "c", "b": "c"})
