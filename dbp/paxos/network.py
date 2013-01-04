# This is a dict of {agent_type: [agents]}
network = {
    "acceptor": [],
    "proposer": [],
    "learner":  [],
}

# This dict allows us to number agents properly
network_num = {}

# This is a dict of {(host, port): agent} to allow us to reverse map (purely
# for debugging purposes
hosts = {}

port_map = {
    'proposer': "224.0.0.2",
    'learner':  "224.0.0.3",
    'acceptor': "224.0.0.4",
}
