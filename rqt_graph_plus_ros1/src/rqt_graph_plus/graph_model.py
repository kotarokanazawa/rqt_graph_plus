import rosgraph

class GraphSnapshot(object):
    def __init__(self):
        self.nodes = set()
        self.topics = {}
        self.publishers = {}
        self.subscribers = {}
        self.node_to_pubs = {}
        self.node_to_subs = {}

    @classmethod
    def from_master(cls):
        snap = cls()
        master = rosgraph.Master('/rqt_graph_plus')
        pubs, subs, _ = master.getSystemState()
        topic_types = dict(master.getTopicTypes())

        for topic, node_list in pubs:
            snap.topics[topic] = topic_types.get(topic, 'unknown')
            snap.publishers[topic] = list(node_list)
            for node in node_list:
                snap.nodes.add(node)
                snap.node_to_pubs.setdefault(node, []).append(topic)

        for topic, node_list in subs:
            snap.topics[topic] = topic_types.get(topic, 'unknown')
            snap.subscribers[topic] = list(node_list)
            for node in node_list:
                snap.nodes.add(node)
                snap.node_to_subs.setdefault(node, []).append(topic)

        return snap
