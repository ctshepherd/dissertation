from dbp.db import DB, NOP, Get, Set, parse_op, InvalidOp
from dbp.test import TestCase


class TestDB(TestCase):
    def test_set(self):
        db = DB()
        db.set("foo", "bar")
        self.assertEqual(db.get("foo"), "bar")

    def test_get(self):
        db = DB({"foo": "bar"})
        self.assertEqual(db.get("foo"), "bar")
        self.assertRaises(KeyError, db.get, "foobar")


class TestOps(TestCase):
    def test_nop(self):
        db = DB()
        d = dict(db._db)
        n = NOP("nop()", ())
        n.perform_op(db)
        self.assertEqual(d, db._db)

    def test_get(self):
        db = DB({"foo": "bar"})
        n = Get("get(foo)", ["foo"])
        ret = n.perform_op(db)
        self.assertEqual(ret, "bar")

    def test_set(self):
        db = DB({"foo": "bar"})
        n = Set("set(foo,baz)", ("foo", "baz"))
        n.perform_op(db)
        self.assertEqual(db.get("foo"), "baz")

    def test_eq(self):
        self.assertEqual(Set("set(foo,baz)", ["foo", "baz"]), Set("set(foo,baz)", ["foo", "baz"]))
        self.assertNotEqual(Set("set(bar,baz)", ["bar", "baz"]), Set("set(foo,baz)", ["foo", "baz"]))
        self.assertNotEqual(Get("get(foo)", ["foo"]), Set("set(foo,baz)", ["foo", "baz"]))


class TestParseOp(TestCase):
    def test_parse(self):
        self.assertEqual(parse_op("get(foo)"), Get("get(foo)", ["foo"]))
        self.assertEqual(parse_op("set(bar,baz)"), Set("set(bar,baz)", ["bar", "baz"]))
        self.assertEqual(parse_op("nop()"), NOP("nop()", []))

    def test_raises(self):
        self.assertRaises(InvalidOp, parse_op, "get()")
        self.assertRaises(InvalidOp, parse_op, "get(foo,bar)")
        self.assertRaises(InvalidOp, parse_op, "set()")
        self.assertRaises(InvalidOp, parse_op, "set(foo)")
        self.assertRaises(InvalidOp, parse_op, "nop(foo)")
        self.assertRaises(InvalidOp, parse_op, "foo(bar)")
        self.assertRaises(InvalidOp, parse_op, "get")
        self.assertRaises(InvalidOp, parse_op, "foo")
