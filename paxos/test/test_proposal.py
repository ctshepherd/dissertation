from paxos.proposal import Proposal
from paxos.test import TestCase


class TestProposal(TestCase):
    def test_serialize(self):
        p = Proposal(1)
        self.assertEqual(p.serialize(), "1,None")
        p = Proposal(2, 3)
        self.assertEqual(p.serialize(), "2,3")
