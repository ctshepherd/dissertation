class Proposal(object):
    """Proposal object"""
    def __init__(self, prop_num, value=None):
        super(Proposal, self).__init__()
        self.prop_num = prop_num
        self.value = value

    def __str__(self):
        return "Proposal(%s: %s)" % (self.prop_num, self.value)

    def __repr__(self):
        return "<%s @ %#lx>" % (self, id(self))
