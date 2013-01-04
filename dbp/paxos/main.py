# from dbp.paxos.message import Promise
# from dbp.paxos.proposal import Proposal
from dbp.paxos.agent import ProposerProtocol, LearnerProtocol, AcceptorProtocol
from twisted.internet import reactor


for k in (ProposerProtocol, ProposerProtocol,
          AcceptorProtocol, AcceptorProtocol, AcceptorProtocol, AcceptorProtocol,
          LearnerProtocol, LearnerProtocol, LearnerProtocol):
    reactor.listenMulticast(8005, k(), listenMultiple=True)
p = ProposerProtocol()
reactor.listenMulticast(8005, p, listenMultiple=True)

#d = p.run(1)


def f(r):
    print "foo: %s" % r


#d.addCallback(f)
# p.writeAll(Promise(Proposal(1)), "learner")
# p.writeAll(Promise(Proposal(1)), "proposer")
# p.writeAll(Promise(Proposal(1)), "acceptor")


def run():
    print "Started"
    reactor.run()

if __name__ == '__main__':
    run()
