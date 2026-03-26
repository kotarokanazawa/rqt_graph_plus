from python_qt_binding.QtCore import Qt, QRectF, QPointF, Signal
from python_qt_binding.QtGui import QColor, QBrush, QPen, QFont, QPainterPath, QFontMetrics
from python_qt_binding.QtWidgets import QGraphicsItem, QGraphicsObject, QGraphicsPathItem

class BaseGraphItem(QGraphicsObject):
    moved = Signal(str, float, float)

    def __init__(self, name, subtitle="", item_kind="node", border_color="#4f86c6",
                 title_pt=12, sub_pt=10, min_width=170, extra_pad=12, parent=None):
        super(BaseGraphItem, self).__init__(parent)
        self.name = name
        self.subtitle = subtitle
        self.item_kind = item_kind
        self.border_color = QColor(border_color)
        self.highlighted = False
        self.dimmed = False
        self._edges = []
        self.pad_x = 14
        self.pad_y = 10
        self.min_width = min_width
        self.extra_pad = extra_pad

        self.title_font = QFont()
        self.title_font.setPointSize(title_pt)
        self.title_font.setBold(True)
        self.sub_font = QFont()
        self.sub_font.setPointSize(sub_pt)

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.setCursor(Qt.OpenHandCursor)

        self.width = self._compute_width()
        self.height = self._compute_height()

    def _compute_width(self):
        fm1 = QFontMetrics(self.title_font)
        fm2 = QFontMetrics(self.sub_font)
        w = max(fm1.horizontalAdvance(self.name), fm2.horizontalAdvance(self.subtitle or ""))
        return max(self.min_width, min(1200, w + self.pad_x * 2 + self.extra_pad))

    def _compute_height(self):
        h = self.pad_y * 2 + 24
        if self.subtitle:
            h += 20
        return h

    def add_edge(self, edge):
        if edge not in self._edges:
            self._edges.append(edge)

    def set_highlight_state(self, highlighted=False, dimmed=False):
        try:
            self.highlighted = highlighted
            self.dimmed = dimmed
            self.update()
        except RuntimeError:
            pass

    def center_left(self):
        rect = self.boundingRect()
        return self.mapToScene(QPointF(rect.left(), rect.center().y()))
    def center_right(self):
        rect = self.boundingRect()
        return self.mapToScene(QPointF(rect.right(), rect.center().y()))
    def center_top(self):
        rect = self.boundingRect()
        return self.mapToScene(QPointF(rect.center().x(), rect.top()))
    def center_bottom(self):
        rect = self.boundingRect()
        return self.mapToScene(QPointF(rect.center().x(), rect.bottom()))

    def best_anchor_to(self, scene_point):
        candidates = {"left": self.center_left(), "right": self.center_right(), "top": self.center_top(), "bottom": self.center_bottom()}
        best_name = None; best_pt = None; best_d = None
        for name, pt in candidates.items():
            d = (pt.x() - scene_point.x())**2 + (pt.y() - scene_point.y())**2
            if best_d is None or d < best_d:
                best_d = d; best_name = name; best_pt = pt
        return best_name, best_pt

    def _border_pen(self):
        if self.highlighted or self.isSelected():
            return QPen(QColor("#f8fafc"), 2.8)
        if self.dimmed:
            return QPen(QColor("#25364d"), 1.0)
        return QPen(self.border_color, 1.8)

    def _fill_brush(self):
        if self.highlighted or self.isSelected():
            return QBrush(QColor("#18253b"))
        if self.dimmed:
            return QBrush(QColor("#0a1321"))
        return QBrush(QColor("#0f1a2e"))

    def _title_color(self):
        return QColor("#93a5c9") if self.dimmed else QColor("#f8fbff")
    def _sub_color(self):
        return QColor("#6f83a7") if self.dimmed else QColor("#b9c9ea")

    def mousePressEvent(self, event):
        self.setCursor(Qt.ClosedHandCursor)
        super(BaseGraphItem, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.OpenHandCursor)
        super(BaseGraphItem, self).mouseReleaseEvent(event)
        self.moved.emit(self.name, float(self.pos().x()), float(self.pos().y()))

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for edge in list(self._edges):
                try:
                    edge.update_path()
                except RuntimeError:
                    pass
        return super(BaseGraphItem, self).itemChange(change, value)

class NodeItem(BaseGraphItem):
    def __init__(self, name, subtitle="", parent=None):
        super(NodeItem, self).__init__(
            name, subtitle, "node", "#5b8fd3",
            title_pt=13, sub_pt=11, min_width=220, extra_pad=24, parent=parent
        )

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter, option, widget):
        rect = self.boundingRect()
        painter.setRenderHint(painter.Antialiasing, True)
        if not self.dimmed:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, 60))
            painter.drawRoundedRect(rect.adjusted(4, 5, 4, 7), 18, 18)
        painter.setPen(self._border_pen())
        painter.setBrush(self._fill_brush())
        painter.drawRoundedRect(rect, 18, 18)
        painter.setPen(self._title_color())
        painter.setFont(self.title_font)
        painter.drawText(QPointF(self.pad_x, self.pad_y + 16), self.name)
        if self.subtitle:
            painter.setPen(self._sub_color())
            painter.setFont(self.sub_font)
            painter.drawText(QPointF(self.pad_x, self.pad_y + 38), self.subtitle)

class TopicItem(BaseGraphItem):
    def __init__(self, name, subtitle="", parent=None):
        super(TopicItem, self).__init__(
            name, subtitle, "topic", "#2dd4bf",
            title_pt=11, sub_pt=9, min_width=170, extra_pad=8, parent=parent
        )

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter, option, widget):
        rect = self.boundingRect()
        painter.setRenderHint(painter.Antialiasing, True)
        if not self.dimmed:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, 58))
            painter.drawRect(rect.adjusted(4, 5, 4, 7))
        painter.setPen(self._border_pen())
        painter.setBrush(self._fill_brush())
        painter.drawRect(rect)
        painter.setPen(self._title_color())
        painter.setFont(self.title_font)
        painter.drawText(QPointF(self.pad_x, self.pad_y + 15), self.name)
        if self.subtitle:
            painter.setPen(self._sub_color())
            painter.setFont(self.sub_font)
            painter.drawText(QPointF(self.pad_x, self.pad_y + 34), self.subtitle)

class EdgeItem(QGraphicsPathItem):
    def __init__(self, src_item, dst_item, color="#5eead4", label_text="", direction_markers=False, parent=None):
        super(EdgeItem, self).__init__(parent)
        self.src_item = src_item
        self.dst_item = dst_item
        self.normal_color = QColor(color)
        self.highlighted = False
        self.dimmed = False
        self.label_text = label_text
        self.direction_markers = direction_markers
        self.setZValue(-1.0)
        self.src_item.add_edge(self)
        self.dst_item.add_edge(self)
        self._label_pos = QPointF(0.0, 0.0)
        self._src_marker_pos = QPointF(0.0, 0.0)
        self._dst_marker_pos = QPointF(0.0, 0.0)
        self.update_path()

    def set_highlight_state(self, highlighted=False, dimmed=False):
        try:
            self.highlighted = highlighted
            self.dimmed = dimmed
            self.update()
        except RuntimeError:
            pass

    def update_path(self):
        _, src = self.src_item.best_anchor_to(self.dst_item.mapToScene(self.dst_item.boundingRect().center()))
        _, dst = self.dst_item.best_anchor_to(src)
        dx = dst.x() - src.x()
        dy = dst.y() - src.y()
        if abs(dx) >= abs(dy):
            c = max(24.0, abs(dx) * 0.35)
            c1 = QPointF(src.x() + (c if dx >= 0 else -c), src.y())
            c2 = QPointF(dst.x() - (c if dx >= 0 else -c), dst.y())
        else:
            c = max(18.0, abs(dy) * 0.35)
            c1 = QPointF(src.x(), src.y() + (c if dy >= 0 else -c))
            c2 = QPointF(dst.x(), dst.y() - (c if dy >= 0 else -c))
        path = QPainterPath(src)
        path.cubicTo(c1, c2, dst)
        self.setPath(path)
        self._label_pos = path.pointAtPercent(0.5)
        self._src_marker_pos = path.pointAtPercent(0.08)
        self._dst_marker_pos = path.pointAtPercent(0.92)

    def paint(self, painter, option, widget):
        painter.setRenderHint(painter.Antialiasing, True)
        if not self.dimmed:
            sh = QPen(QColor(0, 0, 0, 70), 4.8)
            sh.setCapStyle(Qt.RoundCap)
            painter.setPen(sh)
            painter.drawPath(self.path())
        if self.highlighted:
            pen = QPen(QColor("#f8fafc"), 3.1)
        elif self.dimmed:
            pen = QPen(QColor("#23344e"), 1.0)
        else:
            pen = QPen(self.normal_color, 1.8)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawPath(self.path())

        if self.label_text:
            painter.setPen(QColor("#dbe7ff"))
            f = QFont()
            f.setPointSize(10)
            painter.setFont(f)
            painter.drawText(self._label_pos + QPointF(4, -6), self.label_text)

        if self.direction_markers:
            yellow = QColor("#facc15")
            r = 5
            # src side publisher = filled circle
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(yellow))
            painter.drawEllipse(self._src_marker_pos + QPointF(0, -8), r, r)
            # dst side subscriber = hollow circle
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(yellow, 2))
            painter.drawEllipse(self._dst_marker_pos + QPointF(0, -8), r, r)
