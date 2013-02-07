"""Network module.

Network module, mainly contains the DBPNode class, which handles communication through Paxos.
"""

from dbp.paxos.agent import NodeProtocol as PaxosNode
from dbp.util import dbprint

class DBPNode(PaxosNode):
    def __init__(self, manager, *args, **kwargs):
        super(DBPNode, self).__init__(*args, **kwargs)
        self.manager = manager

    def create_instance(self, instance_id):
        i = super(DBPNode, self).create_instance(instance_id)
        i['callback'].addCallback(self.value_learned)
        return i

    def value_learned(self, instance):
        assert instance['status'] == "completed"
        dbprint("passing TX(%s, %s) up" % (instance['instance_id'], instance['value']), level=3)
        self.manager._passup_tx((instance['instance_id'], instance['value']))

    def chase_up(self, instance_id):
        dbprint("chasing up instance %s" % instance_id, level=2)
        if instance_id not in self.instances:
            dbprint("chase up: haven't heard of %s yet, starting again" % instance_id, level=2)
            self.instances[i] = self.create_instance(instance_id)
            self.proposer_start(i, "nop", restart=False)
        else:
            dbprint("chase up: already heard of %s, being mean anyway" % instance_id, level=2)
            i = self.instances[instance_id]
            self.proposer_start(i, "nop", restart=False)
