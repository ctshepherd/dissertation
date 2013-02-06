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
