from agent import Proposer, Learner, Acceptor
from protocol import reactor

p1 = Proposer()
a1 = Acceptor()
l1 = Learner()

print "Started"
p1.run(1)

def run():
    reactor.run()
