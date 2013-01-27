from dbp.paxos import message
from dbp.paxos.message import parse_message, Msg, InvalidMessageException
from dbp.test import TestCase



class TestParseMessage(TestCase):
    skip = True

    def test_errors(self):
        self.assertRaises(InvalidMessageException, parse_message, Msg({"msg_type":"foobar","proposal":"1,2"}))
        self.assertRaises(InvalidMessageException, parse_message, Msg({"msg_type":"promise","proposal":"1"}))


class TestMessage(TestCase):
    skip = True
    def test_ne(self):
        self.assertNotEqual(FakeMessage(Proposal(1)), Prepare(Proposal(1)))
        self.assertNotEqual(Prepare(Proposal(1)), FakeMessage(Proposal(1)))
        self.assertNotEqual(FakeMessage(Proposal(1)), object())
        self.assertNotEqual(object(), FakeMessage(Proposal(1)))
