from collections import defaultdict

def collect_group_members(names):
    members = defaultdict(list)
    for name in names:
        parts = [x for x in name.split("/") if x]
        if len(parts) <= 1:
            continue
        prefix = []
        for p in parts[:-1]:
            prefix.append(p)
            members["/" + "/".join(prefix)].append(name)
    return dict(members)
