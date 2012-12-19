from paxos import message
from paxos.message import parse_message, Message, Promise, Prepare, Accept
from paxos.proposal import Proposal
from paxos.test import TestCase


class FakeMessage(Message):
    msg_type = "fm"


class FMTestCase(TestCase):
    """TestCase subclass that monkeypatches message_types, just to reduce some internal dependencies"""
    def setUp(self):
        self.saved_message_types = message.message_types
        message.message_types = {"fm": FakeMessage}

    def tearDown(self):
        message.message_types = self.saved_message_types


class TestParseMessage(FMTestCase):

    def test_deserialize(self):
        for args in ((1, None), (2, 3), (4, 5)):
            fm = FakeMessage(Proposal(*args))
            res = parse_message("fm:%s" % ",".join(map(str, args)))
            self.assertEqual(fm, res)

    def test_serialization(self):
        # Try to go the whole round trip
        for args in ((1,), (2, 3), (4, 5)):
            fm_orig = FakeMessage(Proposal(*args))
            fm_new = parse_message(fm_orig.serialize())
            self.assertEqual(fm_orig, fm_new)


class TestMessageTypes(TestCase):
    """Test that we can do all of the message types we want"""
    def test_deserialize(self):
        for args in ((1,), (2, 3), (4, 5)):
            for (msg_type, msg_class) in (("prepare", Prepare), ("promise", Promise), ("accept", Accept)):
                m = msg_class(Proposal(*args))
                res = parse_message("%s:%s" % (msg_type, Proposal(*args).serialize()))
                self.assertEqual(m, res)

    def test_serialization(self):
        # Try to go the whole round trip
        for args in ((1,), (2, 3), (4, 5)):
            for (msg_type, msg_class) in (("prepare", Prepare), ("promise", Promise), ("accept", Accept)):
                fm_orig = msg_class(Proposal(*args))
                fm_new = parse_message(fm_orig.serialize())
                self.assertEqual(fm_orig, fm_new)


class TestMessage(TestCase):
    def test_ne(self):
        self.assertNotEqual(FakeMessage(Proposal(1)), Prepare(Proposal(1)))
        self.assertNotEqual(Prepare(Proposal(1)), FakeMessage(Proposal(1)))
        self.assertNotEqual(FakeMessage(Proposal(1)), object())
        self.assertNotEqual(object(), FakeMessage(Proposal(1)))
