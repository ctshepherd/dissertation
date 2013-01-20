from dbp.paxos import message
from dbp.paxos.message import parse_message, LegacyMessage, Msg, Promise, Prepare, AcceptRequest, AcceptNotify, InvalidMessageException, lm
from dbp.paxos.proposal import Proposal
from dbp.test import TestCase


class FakeMessage(LegacyMessage):
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
            res = parse_message(lm("fm:%s" % ",".join(map(str, args))))
            self.assertEqual(fm, res)

    def test_serialization(self):
        # Try to go the whole round trip
        for args in ((1,), (2, 3), (4, 5)):
            fm_orig = FakeMessage(Proposal(*args))
            fm_new = parse_message(fm_orig.serialize())
            self.assertEqual(fm_orig, fm_new)

    def test_errors(self):
        self.assertRaises(InvalidMessageException, parse_message, Msg({"msg_type":"foobar","proposal":"1,2"}))
        self.assertRaises(InvalidMessageException, parse_message, Msg({"msg_type":"promise","proposal":"1"}))


class TestMessageTypes(TestCase):
    """Test that we can do all of the message types we want"""

    def _roundtrip(self, args, msg_type, msg_class):
        """Helper function for test_deserialize"""
        m = msg_class(Proposal(*args))
        res = parse_message(lm("%s:%s" % (msg_type, Proposal(*args).serialize())))
        self.assertEqual(m, res)

    def _roundtrip_s(self, args, msg_class):
        """Helper function for test_serialization"""
        fm_orig = msg_class(Proposal(*args))
        fm_new = parse_message(fm_orig.serialize())
        self.assertEqual(fm_orig, fm_new)

    def test_deserialize(self):
        for args in ((1,), (2, 3), (4, 5)):
            for (msg_type, msg_class) in (("promise", Promise), ("acceptrequest", AcceptRequest), ("acceptnotify", AcceptNotify)):
                self._roundtrip(args, msg_type, msg_class)
        # We have to do Prepare separately because it doesn't take values
        self._roundtrip((1,), "prepare", Prepare)

    def test_serialization(self):
        # Try to go the whole round trip
        for args in ((1,), (2, 3), (4, 5)):
            for msg_class in (Promise, AcceptRequest, AcceptNotify):
                self._roundtrip_s(args, msg_class)
        # We have to do Prepare separately because it doesn't take values
        self._roundtrip_s((1,), Prepare)


class TestMessage(TestCase):
    def test_ne(self):
        self.assertNotEqual(FakeMessage(Proposal(1)), Prepare(Proposal(1)))
        self.assertNotEqual(Prepare(Proposal(1)), FakeMessage(Proposal(1)))
        self.assertNotEqual(FakeMessage(Proposal(1)), object())
        self.assertNotEqual(object(), FakeMessage(Proposal(1)))


class TestPrepare(TestCase):
    def test_sanity(self):
        """Test that we don't allow prepare messages with values"""
        self.assertRaises(InvalidMessageException, Prepare, Proposal(1, 1))
