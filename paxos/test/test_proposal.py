from twisted.trial import unittest
from paxos.proposal import Proposal


class TestProposal(unittest.TestCase):
    def test_serialize(self):
        p = Proposal(1)
        self.assertEqual(p.serialize(), "1,None")
        p = Proposal(2, 3)
        self.assertEqual(p.serialize(), "2,3")
