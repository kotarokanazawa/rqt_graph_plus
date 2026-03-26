import re
import subprocess

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
        return cls._from_ros2()

    @classmethod
    def _run_ros2(cls, args):
        return subprocess.check_output(args, stderr=subprocess.STDOUT, text=True)

    @classmethod
    def _parse_ros2_topic_types(cls):
        out = cls._run_ros2(['ros2', 'topic', 'list', '-t'])
        topic_types = {}
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            m = re.match(r'^(.*?)\s+\[(.*)\]$', line)
            if m:
                topic_types[m.group(1).strip()] = m.group(2).strip()
            else:
                topic_types[line] = 'unknown'
        return topic_types

    @classmethod
    def _parse_ros2_node_info(cls, text):
        pubs = []
        subs = []
        section = None
        for raw in text.splitlines():
            s = raw.strip()
            if not s:
                continue
            if s.startswith('Subscribers:'):
                section = 'sub'
                continue
            if s.startswith('Publishers:'):
                section = 'pub'
                continue
            if s.endswith(':') and s[:-1] in (
                'Service Servers', 'Service Clients', 'Action Servers',
                'Action Clients', 'Clients', 'Servers'
            ):
                section = None
                continue
            if section in ('pub', 'sub'):
                m = re.match(r'^([^\s:]+)\s*:\s*(.+)$', s)
                if m:
                    topic = m.group(1).strip()
                    if section == 'pub':
                        pubs.append(topic)
                    else:
                        subs.append(topic)
        return pubs, subs

    @classmethod
    def _from_ros2(cls):
        snap = cls()
        topic_types = cls._parse_ros2_topic_types()

        node_out = cls._run_ros2(['ros2', 'node', 'list'])
        nodes = [line.strip() for line in node_out.splitlines() if line.strip()]
        for node in nodes:
            snap.nodes.add(node)
            try:
                info = cls._run_ros2(['ros2', 'node', 'info', node])
            except subprocess.CalledProcessError:
                continue
            pubs, subs = cls._parse_ros2_node_info(info)

            for topic in pubs:
                snap.topics[topic] = topic_types.get(topic, 'unknown')
                snap.publishers.setdefault(topic, []).append(node)
                snap.node_to_pubs.setdefault(node, []).append(topic)

            for topic in subs:
                snap.topics[topic] = topic_types.get(topic, 'unknown')
                snap.subscribers.setdefault(topic, []).append(node)
                snap.node_to_subs.setdefault(node, []).append(topic)

        return snap
