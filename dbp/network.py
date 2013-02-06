"""Network module.

Network module, mainly contains the DBPNode class, which handles communication through Paxos.
"""

from dbp.paxos.agent import NodeProtocol as PaxosNode

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
        self.manager._passup_tx((instance['instance_id'], instance['value']))
