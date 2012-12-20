from dbp.dbp import DB, DBP
from twisted.trial import unittest

class TestDB(unittest.TestCase):
    def test_set(self):
        db = DB()
        db.set("foo", "bar")
        self.assertEqual(db.get("foo"), "bar")
        self.assertRaises(KeyError, db.get, "foobar")
