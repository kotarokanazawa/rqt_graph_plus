import math
from collections import defaultdict, deque

OUTER_MARGIN = 120.0
CELL_W = 220.0
CELL_H = 120.0
RING_RADIUS_CELLS = 4
COMP_GAP_X = 8
COMP_GAP_Y = 6

def compute_used_topics(snapshot, visible_nodes, visible_topics, nodes_only=False, prune_isolated_topics=True):
    if nodes_only or not prune_isolated_topics:
        return list(visible_topics)
    vnodes = set(visible_nodes)
    used = []
    for t in visible_topics:
        pubs = [n for n in snapshot.publishers.get(t, []) if n in vnodes]
        subs = [n for n in snapshot.subscribers.get(t, []) if n in vnodes]
        if pubs and subs:
            used.append(t)
    return used

def _build_adj(snapshot, visible_nodes, visible_topics, nodes_only=False):
    adj = defaultdict(set)
    if nodes_only:
        for t in visible_topics:
            pubs = [n for n in snapshot.publishers.get(t, []) if n in visible_nodes]
            subs = [n for n in snapshot.subscribers.get(t, []) if n in visible_nodes]
            for p in pubs:
                for s in subs:
                    if p == s:
                        continue
                    adj[p].add(s)
                    adj[s].add(p)
    else:
        for t in visible_topics:
            tk = ("topic", t)
            for n in snapshot.publishers.get(t, []):
                if n in visible_nodes:
                    nk = ("node", n)
                    adj[nk].add(tk)
                    adj[tk].add(nk)
            for n in snapshot.subscribers.get(t, []):
                if n in visible_nodes:
                    nk = ("node", n)
                    adj[nk].add(tk)
                    adj[tk].add(nk)
    return adj

def _connected_components(adj, vertices):
    seen = set()
    comps = []
    for v in vertices:
        if v in seen:
            continue
        q = deque([v])
        seen.add(v)
        comp = []
        while q:
            cur = q.popleft()
            comp.append(cur)
            for nxt in adj.get(cur, []):
                if nxt not in seen:
                    seen.add(nxt)
                    q.append(nxt)
        comps.append(comp)
    return comps

def _seed_for_component(adj, comp):
    return max(comp, key=lambda x: (len(adj.get(x, [])), str(x)))

def _bfs_layers(adj, seed):
    q = deque([seed])
    dist = {seed: 0}
    while q:
        cur = q.popleft()
        for nxt in sorted(adj.get(cur, []), key=lambda x: (-len(adj.get(x, [])), str(x))):
            if nxt not in dist:
                dist[nxt] = dist[cur] + 1
                q.append(nxt)
    return dist

def _cell_size_for_item(name, widths, heights):
    w = widths.get(name, 180.0)
    h = heights.get(name, 64.0)
    cw = max(1, int(math.ceil((w + 40.0) / CELL_W)))
    ch = max(1, int(math.ceil((h + 30.0) / CELL_H)))
    return cw, ch

def _free_at(occ, gx, gy, gw, gh):
    for x in range(gx, gx + gw):
        for y in range(gy, gy + gh):
            if (x, y) in occ:
                return False
    return True

def _occupy(occ, gx, gy, gw, gh, name):
    for x in range(gx, gx + gw):
        for y in range(gy, gy + gh):
            occ[(x, y)] = name

def _candidate_cells_for_layer(layer):
    if layer == 0:
        return [(0, 0)]
    r = max(1, layer * RING_RADIUS_CELLS)
    pts = []
    # perimeter spiral/ring candidates
    for x in range(-r, r + 1):
        pts.append((x, -r))
        pts.append((x, r))
    for y in range(-r + 1, r):
        pts.append((-r, y))
        pts.append((r, y))
    # unique, ordered by angle then radius tie
    seen = set()
    out = []
    for p in pts:
        if p not in seen:
            seen.add(p)
            out.append(p)
    out.sort(key=lambda p: (math.atan2(p[1], p[0]), abs(p[0]) + abs(p[1])))
    return out

def _try_place_near_ring(occ, layer, gw, gh):
    candidates = _candidate_cells_for_layer(layer)
    for gx, gy in candidates:
        if _free_at(occ, gx, gy, gw, gh):
            return gx, gy
    # fallback expanding search
    radius = max(1, layer * RING_RADIUS_CELLS)
    limit = radius + 50
    for r in range(radius, limit + 1):
        for x in range(-r, r + 1):
            for y in (-r, r):
                if _free_at(occ, x, y, gw, gh):
                    return x, y
        for y in range(-r + 1, r):
            for x in (-r, r):
                if _free_at(occ, x, y, gw, gh):
                    return x, y
    raise RuntimeError("could not find free occupancy cell")

def _layout_component(snapshot, adj, comp, widths, heights, nodes_only=False):
    seed = _seed_for_component(adj, comp)
    dist = _bfs_layers(adj, seed)
    layers = defaultdict(list)
    for v in comp:
        layers[dist.get(v, 999)].append(v)

    # sort each layer by connectivity, then name
    for k in list(layers.keys()):
        layers[k] = sorted(layers[k], key=lambda x: (-len(adj.get(x, [])), str(x)))

    occ = {}
    placements = {}
    max_layer = max(layers.keys()) if layers else 0
    for layer in range(0, max_layer + 1):
        for v in layers[layer]:
            name = v if nodes_only else v[1]
            gw, gh = _cell_size_for_item(name, widths, heights)
            gx, gy = _try_place_near_ring(occ, layer, gw, gh)
            _occupy(occ, gx, gy, gw, gh, name)
            placements[name] = (gx, gy, gw, gh)

    min_x = min(gx for gx, gy, gw, gh in placements.values()) if placements else 0
    min_y = min(gy for gx, gy, gw, gh in placements.values()) if placements else 0

    out = {}
    for name, (gx, gy, gw, gh) in placements.items():
        px = (gx - min_x) * CELL_W + OUTER_MARGIN
        py = (gy - min_y) * CELL_H + OUTER_MARGIN
        # center box within its occupied cell block
        w = widths.get(name, 180.0)
        h = heights.get(name, 64.0)
        px += (gw * CELL_W - w) / 2.0
        py += (gh * CELL_H - h) / 2.0
        out[name] = (px, py)

    comp_w = 0.0
    comp_h = 0.0
    for name, (px, py) in out.items():
        comp_w = max(comp_w, px + widths.get(name, 180.0))
        comp_h = max(comp_h, py + heights.get(name, 64.0))
    return out, comp_w + OUTER_MARGIN, comp_h + OUTER_MARGIN

def compute_auto_positions(snapshot, visible_nodes, visible_topics, widths, heights, nodes_only=False):
    if nodes_only:
        vertices = list(visible_nodes)
    else:
        vertices = [("node", n) for n in visible_nodes] + [("topic", t) for t in visible_topics]

    adj = _build_adj(snapshot, visible_nodes, visible_topics, nodes_only=nodes_only)
    comps = _connected_components(adj, vertices)
    comps.sort(key=lambda comp: (-len(comp), -max(len(adj.get(v, [])) for v in comp), str(comp[0])))

    packed = {}
    cur_x = OUTER_MARGIN
    cur_y = OUTER_MARGIN
    row_h = 0.0
    pack_width = 5200.0

    for comp in comps:
        pos, comp_w, comp_h = _layout_component(snapshot, adj, comp, widths, heights, nodes_only=nodes_only)
        if cur_x > OUTER_MARGIN and cur_x + comp_w > pack_width:
            cur_x = OUTER_MARGIN
            cur_y += row_h + COMP_GAP_Y * CELL_H
            row_h = 0.0
        for name, (x, y) in pos.items():
            packed[name] = (x + cur_x, y + cur_y)
        cur_x += comp_w + COMP_GAP_X * CELL_W
        row_h = max(row_h, comp_h)

    return packed, False
