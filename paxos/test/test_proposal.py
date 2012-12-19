from paxos.proposal import Proposal
from paxos.test import TestCase


class TestProposal(TestCase):
    def test_serialize(self):
        p = Proposal(1)
        self.assertEqual(p.serialize(), "1,None")
        p = Proposal(2, 3)
        self.assertEqual(p.serialize(), "2,3")

    def test_eq(self):
        self.assertEqual(Proposal(1), Proposal(1))
        self.assertEqual(Proposal(1, 1), Proposal(1, 1))

    def test_ne(self):
        self.assertNotEqual(Proposal(1), Proposal(2))
        self.assertNotEqual(Proposal(2), Proposal(1))
        self.assertNotEqual(Proposal(1, 1), Proposal(1, 2))
        self.assertNotEqual(Proposal(1, 2), Proposal(1, 1))
        self.assertNotEqual(Proposal(1), object())
        self.assertNotEqual(object(), Proposal(1))

    def test_hash(self):
        o = object()
        d = {}
        d[Proposal(1)] = o
        self.assertEqual(d[Proposal(1)], o)
        self.assertRaises(KeyError, d.__getitem__, Proposal(2))
