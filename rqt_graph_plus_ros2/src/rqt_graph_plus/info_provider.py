import subprocess

def _run(args):
    return subprocess.check_output(args, stderr=subprocess.STDOUT, text=True)

def get_node_info_text(node_name, snapshot=None):
    lines = ["Node", node_name, ""]
    try:
        desc = _run(['ros2', 'node', 'info', node_name])
        lines.append(desc.strip())
        lines.append("")
    except Exception as exc:
        lines.append("ros2 node info failed: {}".format(exc))
        lines.append("")
    if snapshot is not None:
        pubs = sorted(snapshot.node_to_pubs.get(node_name, []))
        subs = sorted(snapshot.node_to_subs.get(node_name, []))
        if pubs:
            lines += ["Publish:"] + ["  " + x for x in pubs] + [""]
        if subs:
            lines += ["Subscribe:"] + ["  " + x for x in subs] + [""]
    return "\n".join(lines)

def get_topic_info_text(topic_name, snapshot=None):
    lines = ["Topic", topic_name, ""]
    try:
        desc = _run(['ros2', 'topic', 'info', '-v', topic_name])
        lines.append(desc.strip())
        lines.append("")
    except Exception as exc:
        lines.append("ros2 topic info failed: {}".format(exc))
        lines.append("")
    if snapshot is not None:
        lines += ["Type: {}".format(snapshot.topics.get(topic_name, "unknown")), ""]
        pubs = sorted(snapshot.publishers.get(topic_name, []))
        subs = sorted(snapshot.subscribers.get(topic_name, []))
        lines += ["Publishers: {}".format(len(pubs))] + ["  " + x for x in pubs] + [""]
        lines += ["Subscribers: {}".format(len(subs))] + ["  " + x for x in subs]
    return "\n".join(lines)
