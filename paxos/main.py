from agent import Proposer, Learner, Acceptor
from protocol import reactor

p1 = Proposer()
p2 = Proposer()
a1 = Acceptor()
a2 = Acceptor()
a3 = Acceptor()
a4 = Acceptor()
l1 = Learner()
l2 = Learner()
l3 = Learner()

print "Started"
p1.run(1)
p2.run(1)
p1.run(3)

def run():
    reactor.run()
