from dbp.core import DBP
from dbp.manager import TXManager
from paxos.test import TestCase
from paxos.util import cb
from twisted.trial.unittest import SkipTest


class TestDBP(TestCase):

    def test_sync_db(self):
        p = DBP()

        p.queue((1, "a = b"))
        self.assertEqual(p.db._db, {})
        p.sync_db()
        self.assertEqual(p.db._db, {'a': 'b'})

        p.queue((2, "b = a"))
        p.queue((3, "a = a"))
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
        p = DBP()
        p.manager = TXManager([(1, "a = b"), (2, "b = c"), (3, "a = c")])
        d = p.execute("b = a")
        d.addCallback(cb(self.assertEqual, (p.db._db, {"a": "c", "b": "a"})))

        return d

    def test_execute2(self):
        raise SkipTest('hangs test at the moment')
        p = DBP()
        p.manager = TXManager([(1, "a = b"), (2, "b = c"), (3, "a = c")])
        d = p.execute("b = a")
        d.addCallback(lambda r: p.execute("b = c"))
        d.addCallback(cb(self.assertEqual, (p.db._db, {"a": "c", "b": "c"})))

        return d
