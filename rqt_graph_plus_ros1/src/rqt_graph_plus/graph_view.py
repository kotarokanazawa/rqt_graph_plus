import math
from collections import deque
from python_qt_binding.QtCore import Qt, Signal, QRectF
from python_qt_binding.QtGui import QPainter, QColor, QPen, QFont
from python_qt_binding.QtWidgets import QGraphicsView, QGraphicsScene, QMenu, QGraphicsObject

from .graph_items import NodeItem, TopicItem, EdgeItem
from .layout_engine import compute_auto_positions, compute_used_topics
from .namespace_groups import collect_group_members

class NamespaceGroupItem(QGraphicsObject):
    movedMembers = Signal(float, float)
    selectMembers = Signal(list)

    def __init__(self, label, rect, level=0, members=None, parent=None):
        super(NamespaceGroupItem, self).__init__(parent)
        self.label = label
        self._rect = rect
        self.level = level
        self.members = members or []
        self.setZValue(-10 - level)
        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)

    def boundingRect(self):
        return self._rect

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing, True)
        colors = ["#3a557d", "#2f4768", "#253a56", "#1d3048"]
        color = colors[min(self.level, len(colors)-1)]
        pen = QPen(QColor(color), 1.4, Qt.DashLine)
        if self.isSelected():
            pen = QPen(QColor("#dbeafe"), 2.0, Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(self._rect, 14, 14)
        painter.setPen(QColor("#a7bde6"))
        f = QFont()
        f.setPointSize(max(10, 12 - min(self.level, 2)))
        painter.setFont(f)
        painter.drawText(self._rect.adjusted(8, 4, -8, -4), self.label)

    def mousePressEvent(self, event):
        self.selectMembers.emit(list(self.members))
        super(NamespaceGroupItem, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        delta = event.scenePos() - event.lastScenePos()
        if delta.x() != 0.0 or delta.y() != 0.0:
            self.movedMembers.emit(delta.x(), delta.y())
        super(NamespaceGroupItem, self).mouseMoveEvent(event)

class GraphView(QGraphicsView):
    itemSelected = Signal(str)
    itemMoved = Signal(str, float, float)
    requestInfo = Signal(str, str)
    requestEcho = Signal(str)
    requestHide = Signal(str, str)

    def __init__(self, parent=None):
        super(GraphView, self).__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setInteractive(True)

        self.node_items = {}
        self.topic_items = {}
        self.edge_items = []
        self.edge_map = []
        self.group_items = []
        self.last_used_graphviz = False
        self._panning = False
        self._pan_start = None
        self._rebuilding = False
        self._syncing_group_selection = False
        self._moving_group = False
        self._scene.selectionChanged.connect(self._on_selection_changed)

    def clear_graph(self):
        self._rebuilding = True
        try:
            try:
                self._scene.selectionChanged.disconnect(self._on_selection_changed)
            except Exception:
                pass
            self._scene.clear()
            self.node_items.clear()
            self.topic_items.clear()
            self.edge_items = []
            self.edge_map = []
            self.group_items = []
        finally:
            self._scene.selectionChanged.connect(self._on_selection_changed)
            self._rebuilding = False

    def _floating_nodes(self, snapshot, visible_nodes, visible_topics):
        topic_set = set(visible_topics)
        floating = []
        for n in visible_nodes:
            has_pub = any(t in topic_set for t in snapshot.node_to_pubs.get(n, []))
            has_sub = any(t in topic_set for t in snapshot.node_to_subs.get(n, []))
            if not has_pub and not has_sub:
                floating.append(n)
        return floating

    def _highlighted_names(self):
        names = set()
        for name, item in self.node_items.items():
            if getattr(item, "highlighted", False) or item.isSelected():
                names.add(name)
        for name, item in self.topic_items.items():
            if getattr(item, "highlighted", False) or item.isSelected():
                names.add(name)
        return names

    def _zoom_to_names(self, names):
        rect = None
        for name in names:
            item = self.node_items.get(name) or self.topic_items.get(name)
            if item is None:
                continue
            r = item.sceneBoundingRect().adjusted(-30, -30, 30, 30)
            rect = r if rect is None else rect.united(r)
        if rect is not None and rect.width() > 0 and rect.height() > 0:
            self.fitInView(rect, Qt.KeepAspectRatio)

    def _is_rviz_related_node(self, name):
        lower = name.lower()
        return "rviz" in lower or lower.startswith("/rviz") or lower.startswith("rviz")

    def _is_rviz_related_topic(self, name):
        lower = name.lower()
        return "/rviz" in lower or lower.startswith("/rviz") or lower.startswith("rviz") or "rviz" in lower

    def populate_from_snapshot(self, snapshot, positions=None, filter_text="", show_rosout=True, show_self=True,
                               show_clock=False, show_rviz=True, show_floating=False, hidden_nodes=None, hidden_topics=None,
                               nodes_only=False, prune_isolated_topics=True, draw_namespaces=True):
        self.clear_graph()
        positions = positions or {}
        hidden_nodes = hidden_nodes or set()
        hidden_topics = hidden_topics or set()
        f = (filter_text or "").strip().lower()

        visible_nodes = sorted(snapshot.nodes)
        visible_topics = sorted(snapshot.topics.keys())

        if not show_self:
            visible_nodes = [n for n in visible_nodes if "rqt_graph_plus" not in n]
        if not show_rosout:
            visible_nodes = [n for n in visible_nodes if n != "/rosout"]
            visible_topics = [t for t in visible_topics if t not in ("/rosout", "/rosout_agg")]
        if not show_clock:
            visible_topics = [t for t in visible_topics if t not in ("/clock", "clock")]
        if not show_rviz:
            visible_nodes = [n for n in visible_nodes if not self._is_rviz_related_node(n)]
            visible_topics = [t for t in visible_topics if not self._is_rviz_related_topic(t)]

        visible_nodes = [n for n in visible_nodes if n not in hidden_nodes]
        visible_topics = [t for t in visible_topics if t not in hidden_topics]

        if f:
            visible_nodes = [n for n in visible_nodes if f in n.lower()]
            visible_topics = [t for t in visible_topics if f in t.lower()]

        visible_topics = compute_used_topics(snapshot, visible_nodes, visible_topics, nodes_only=nodes_only,
                                            prune_isolated_topics=prune_isolated_topics)

        if not show_floating:
            floating = set(self._floating_nodes(snapshot, visible_nodes, visible_topics))
            visible_nodes = [n for n in visible_nodes if n not in floating]

        widths = {}
        heights = {}
        for n in visible_nodes:
            tmp = NodeItem(n, "node")
            widths[n] = tmp.width
            heights[n] = tmp.height
        if not nodes_only:
            for t in visible_topics:
                tmp = TopicItem(t, snapshot.topics.get(t, "unknown"))
                widths[t] = tmp.width
                heights[t] = tmp.height

        auto_positions, used_graphviz = compute_auto_positions(snapshot, visible_nodes, visible_topics, widths, heights, nodes_only=nodes_only)
        self.last_used_graphviz = used_graphviz

        for node_name in visible_nodes:
            item = NodeItem(node_name, "node")
            px, py = positions.get(node_name, auto_positions.get(node_name, (0, 0)))
            item.setPos(px, py)
            item.moved.connect(self.itemMoved.emit)
            self._scene.addItem(item)
            self.node_items[node_name] = item

        if not nodes_only:
            for topic_name in visible_topics:
                item = TopicItem(topic_name, snapshot.topics.get(topic_name, "unknown"))
                px, py = positions.get(topic_name, auto_positions.get(topic_name, (280, 0)))
                item.setPos(px, py)
                item.moved.connect(self.itemMoved.emit)
                self._scene.addItem(item)
                self.topic_items[topic_name] = item

            for topic_name, pubs in snapshot.publishers.items():
                if topic_name not in self.topic_items:
                    continue
                for node_name in pubs:
                    if node_name in self.node_items:
                        edge = EdgeItem(self.node_items[node_name], self.topic_items[topic_name], color="#5b8fd3")
                        self._scene.addItem(edge)
                        self.edge_items.append(edge)
                        self.edge_map.append((node_name, topic_name, edge))

            for topic_name, subs in snapshot.subscribers.items():
                if topic_name not in self.topic_items:
                    continue
                for node_name in subs:
                    if node_name in self.node_items:
                        edge = EdgeItem(self.topic_items[topic_name], self.node_items[node_name], color="#2dd4bf")
                        self._scene.addItem(edge)
                        self.edge_items.append(edge)
                        self.edge_map.append((topic_name, node_name, edge))
        else:
            node_pairs = set()
            for topic_name in visible_topics:
                pubs = [n for n in snapshot.publishers.get(topic_name, []) if n in self.node_items]
                subs = [n for n in snapshot.subscribers.get(topic_name, []) if n in self.node_items]
                for p in pubs:
                    for s in subs:
                        if p == s:
                            continue
                        key = (p, s, topic_name)
                        if key in node_pairs:
                            continue
                        node_pairs.add(key)
                        edge = EdgeItem(self.node_items[p], self.node_items[s], color="#6ee7b7", label_text=topic_name, direction_markers=True)
                        self._scene.addItem(edge)
                        self.edge_items.append(edge)
                        self.edge_map.append((p, s, edge))

        if draw_namespaces:
            self._add_namespace_groups(list(self.node_items.keys()) + list(self.topic_items.keys()))

        self._scene.setSceneRect(self._scene.itemsBoundingRect().adjusted(-180, -180, 180, 180))
        self._apply_neighbor_highlight()

    def _add_namespace_groups(self, names):
        members_map = collect_group_members(names)
        for ns in sorted(members_map.keys(), key=lambda s: s.count("/"), reverse=True):
            member_names = members_map[ns]
            items = []
            for name in member_names:
                if name in self.node_items:
                    items.append(self.node_items[name])
                elif name in self.topic_items:
                    items.append(self.topic_items[name])
            if len(items) < 2:
                continue
            rect = None
            for it in items:
                r = it.sceneBoundingRect().adjusted(-22, -28, 22, 20)
                rect = r if rect is None else rect.united(r)
            if rect is not None:
                level = max(0, ns.count("/") - 1)
                group = NamespaceGroupItem(ns, QRectF(rect), level=level, members=member_names)
                group.movedMembers.connect(lambda dx, dy, names=member_names: self._move_group_members(names, dx, dy))
                group.selectMembers.connect(self._select_group_members)
                self._scene.addItem(group)
                self.group_items.append(group)

    def _select_group_members(self, member_names):
        self._syncing_group_selection = True
        try:
            self._scene.clearSelection()
            for name in member_names:
                item = self.node_items.get(name) or self.topic_items.get(name)
                if item is not None:
                    item.setSelected(True)
        finally:
            self._syncing_group_selection = False

    def _move_group_members(self, member_names, dx, dy):
        if self._moving_group:
            return
        self._moving_group = True
        try:
            for name in member_names:
                item = self.node_items.get(name) or self.topic_items.get(name)
                if item is None:
                    continue
                try:
                    item.blockSignals(True)
                    item.setPos(item.pos().x() + dx, item.pos().y() + dy)
                    self.itemMoved.emit(name, float(item.pos().x()), float(item.pos().y()))
                finally:
                    item.blockSignals(False)
            for edge in list(self.edge_items):
                try:
                    edge.update_path()
                except RuntimeError:
                    pass
        finally:
            self._moving_group = False

    def _apply_neighbor_highlight(self):
        if self._rebuilding:
            return
        items = [it for it in self._scene.selectedItems() if hasattr(it, "name")]
        selected_name = getattr(items[0], "name", None) if items else None
        all_items = list(self.node_items.values()) + list(self.topic_items.values())
        if not selected_name:
            for it in list(all_items):
                try:
                    it.set_highlight_state(False, False)
                except RuntimeError:
                    pass
            for e in list(self.edge_items):
                try:
                    e.set_highlight_state(False, False)
                except RuntimeError:
                    pass
            return
        neighbors = {selected_name}
        active = set()
        for s, d, e in list(self.edge_map):
            if s == selected_name or d == selected_name:
                neighbors.add(s); neighbors.add(d); active.add(e)
        for n, it in list(self.node_items.items()):
            try:
                it.set_highlight_state(n in neighbors, n not in neighbors)
            except RuntimeError:
                pass
        for n, it in list(self.topic_items.items()):
            try:
                it.set_highlight_state(n in neighbors, n not in neighbors)
            except RuntimeError:
                pass
        for e in list(self.edge_items):
            try:
                e.set_highlight_state(e in active, e not in active)
            except RuntimeError:
                pass

    def drawBackground(self, painter, rect):
        super(GraphView, self).drawBackground(painter, rect)
        painter.save()
        painter.fillRect(rect, QColor("#070c17"))
        minor = 28; major = minor * 4
        left = int(math.floor(rect.left())); top = int(math.floor(rect.top()))
        right = int(math.ceil(rect.right())); bottom = int(math.ceil(rect.bottom()))
        minor_pen = QPen(QColor(18, 34, 58, 70), 1)
        major_pen = QPen(QColor(36, 64, 104, 90), 1)
        x = left - (left % minor)
        while x < right:
            painter.setPen(major_pen if x % major == 0 else minor_pen)
            painter.drawLine(x, top, x, bottom); x += minor
        y = top - (top % minor)
        while y < bottom:
            painter.setPen(major_pen if y % major == 0 else minor_pen)
            painter.drawLine(left, y, right, y); y += minor
        painter.restore()

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.pos())
        target = item
        while target is not None and not hasattr(target, "name"):
            target = target.parentItem()
        if target is not None and hasattr(target, "name"):
            names = self._highlighted_names()
            if target.name not in names:
                names.add(target.name)
            self._zoom_to_names(names)
            event.accept()
            return
        super(GraphView, self).mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.SizeAllCursor)
            event.accept()
            return
        super(GraphView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning and self._pan_start is not None:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        super(GraphView, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton and self._panning:
            self._panning = False
            self._pan_start = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super(GraphView, self).mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        if item is None:
            return super(GraphView, self).contextMenuEvent(event)
        target = item
        while target is not None and not hasattr(target, "item_kind"):
            target = target.parentItem()
        if target is None:
            return super(GraphView, self).contextMenuEvent(event)
        menu = QMenu(self)
        info_action = menu.addAction("Info")
        echo_action = menu.addAction("Echo") if target.item_kind == "topic" else None
        hide_action = menu.addAction("Hide temporarily")
        sel = menu.exec_(self.mapToGlobal(event.pos()))
        if sel == info_action:
            self.requestInfo.emit(target.item_kind, target.name)
        elif echo_action is not None and sel == echo_action:
            self.requestEcho.emit(target.name)
        elif sel == hide_action:
            self.requestHide.emit(target.item_kind, target.name)
        event.accept()

    def _on_selection_changed(self):
        if self._rebuilding or self._syncing_group_selection:
            return
        items = [it for it in self._scene.selectedItems() if hasattr(it, "name")]
        if not items:
            self.itemSelected.emit("")
            self._apply_neighbor_highlight()
            return
        item = items[0]
        txt = getattr(item, "name", "")
        subtitle = getattr(item, "subtitle", "")
        if txt and subtitle:
            txt += "\n" + subtitle
        self.itemSelected.emit(txt or "edge")
        self._apply_neighbor_highlight()
