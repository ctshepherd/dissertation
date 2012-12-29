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

    def __eq__(self, other):
        if not isinstance(other, Proposal):
            return NotImplemented
        return (self.prop_num == other.prop_num and
                self.value    == other.value)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        v = self.value
        if v is None:
            v = 0
        return self.prop_num*10000 + v

    def serialize(self):
        return "%s,%s" % (self.prop_num, self.value)
