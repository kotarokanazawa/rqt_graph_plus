import traceback
import subprocess

from python_qt_binding.QtCore import QTimer, Qt
from python_qt_binding.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTextEdit, QFrame, QCheckBox
)

from .styles import APP_STYLE
from .graph_model import GraphSnapshot
from .graph_view import GraphView
from .info_provider import get_node_info_text, get_topic_info_text
from .ros_env import is_ros2
import subprocess

class MainWidget(QWidget):
    def __init__(self):
        super(MainWidget, self).__init__()
        self.setWindowTitle("rqt_graph_plus")
        self.setStyleSheet(APP_STYLE)
        self.positions = {}
        self.snapshot = None
        self.first_load = True
        self.hidden_nodes = set()
        self.hidden_topics = set()
        self._drag_pause_counter = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh_graph)
        self._build_ui()
        self._timer.start(2000)
        self.refresh_graph()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        top = QFrame()
        top.setObjectName("topBar")
        top_layout = QVBoxLayout(top)
        top_layout.setContentsMargins(10, 8, 10, 8)
        top_layout.setSpacing(6)

        row1 = QHBoxLayout()
        title = QLabel("graph+")
        title.setObjectName("titleLabel")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("filter")
        self.search_edit.textChanged.connect(self.refresh_graph)
        self.refresh_btn = QPushButton("Refresh")
        self.fit_btn = QPushButton("Fit")
        self.relayout_btn = QPushButton("Relayout")
        self.pause_btn = QPushButton("Pause")
        self.show_all_btn = QPushButton("Show hidden")
        self.refresh_btn.clicked.connect(self.refresh_graph)
        self.fit_btn.clicked.connect(self._fit_graph)
        self.relayout_btn.clicked.connect(self._clear_positions_and_refresh)
        self.pause_btn.clicked.connect(self._toggle_pause)
        self.show_all_btn.clicked.connect(self._show_all_hidden)
        row1.addWidget(title, 0)
        row1.addWidget(self.search_edit, 1)
        row1.addWidget(self.refresh_btn)
        row1.addWidget(self.fit_btn)
        row1.addWidget(self.relayout_btn)
        row1.addWidget(self.pause_btn)
        row1.addWidget(self.show_all_btn)

        row2 = QHBoxLayout()
        self.show_rosout_cb = QCheckBox("rosout")
        self.show_self_cb = QCheckBox("self")
        self.show_clock_cb = QCheckBox("clock")
        self.show_rviz_cb = QCheckBox("rviz")
        self.show_floating_cb = QCheckBox("floating nodes")
        self.nodes_only_cb = QCheckBox("nodes only")
        self.prune_topics_cb = QCheckBox("prune isolated topics")
        self.namespace_cb = QCheckBox("namespace group")
        self.show_rosout_cb.setChecked(False)
        self.show_self_cb.setChecked(False)
        self.show_clock_cb.setChecked(False)
        self.show_rviz_cb.setChecked(True)
        self.show_floating_cb.setChecked(False)
        self.nodes_only_cb.setChecked(False)
        self.prune_topics_cb.setChecked(True)
        self.namespace_cb.setChecked(True)
        for w in [self.show_rosout_cb, self.show_self_cb, self.show_clock_cb,
                  self.show_rviz_cb, self.show_floating_cb, self.prune_topics_cb, self.namespace_cb]:
            w.toggled.connect(self.refresh_graph)
        self.nodes_only_cb.toggled.connect(self._clear_positions_and_refresh)
        row2.addWidget(self.show_rosout_cb)
        row2.addWidget(self.show_self_cb)
        row2.addWidget(self.show_clock_cb)
        row2.addWidget(self.show_rviz_cb)
        row2.addWidget(self.show_floating_cb)
        row2.addWidget(self.nodes_only_cb)
        row2.addWidget(self.prune_topics_cb)
        row2.addWidget(self.namespace_cb)
        row2.addStretch(1)

        top_layout.addLayout(row1)
        top_layout.addLayout(row2)

        body = QHBoxLayout()
        self.graph = GraphView()
        self.graph.itemSelected.connect(self._on_item_selected)
        self.graph.itemMoved.connect(self._on_item_moved)
        self.graph.requestInfo.connect(self._show_info)
        self.graph.requestEcho.connect(self._run_echo)
        self.graph.requestHide.connect(self._hide_item)

        side = QFrame()
        side.setObjectName("sidePanel")
        side_layout = QVBoxLayout(side)
        info_title = QLabel("Selection")
        info_title.setObjectName("titleLabel")
        info_sub = QLabel("middle button: pan / double-click: zoom highlighted")
        info_sub.setObjectName("subLabel")
        self.info_box = QTextEdit()
        self.info_box.setReadOnly(True)
        self.info_box.setPlainText("No selection")
        self.status_label = QLabel("status: ready")
        self.status_label.setObjectName("subLabel")
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        side_layout.addWidget(info_title)
        side_layout.addWidget(info_sub)
        side_layout.addWidget(self.info_box, 1)
        side_layout.addWidget(self.status_label)
        body.addWidget(self.graph, 5)
        body.addWidget(side, 2)

        root.addWidget(top)
        root.addLayout(body, 1)

    def _toggle_pause(self):
        if self._timer.isActive():
            self._timer.stop()
            self.pause_btn.setText("Resume")
            self.status_label.setText("status: paused")
        else:
            self._timer.start(2000)
            self.pause_btn.setText("Pause")
            self.refresh_graph()

    def _fit_graph(self):
        if self.graph.scene() is not None:
            self.graph.fitInView(self.graph.scene().sceneRect(), Qt.KeepAspectRatio)

    def _show_all_hidden(self):
        self.hidden_nodes.clear()
        self.hidden_topics.clear()
        self.refresh_graph()

    def _clear_positions_and_refresh(self):
        self.positions = {}
        self.first_load = True
        self.refresh_graph()

    def _on_item_selected(self, text):
        self.info_box.setPlainText(text or "No selection")

    def _on_item_moved(self, name, x, y):
        self.positions[name] = (x, y)
        self._drag_pause_counter = 2

    def _show_info(self, item_kind, name):
        if item_kind == "node":
            self.info_box.setPlainText(get_node_info_text(name, self.snapshot))
        else:
            self.info_box.setPlainText(get_topic_info_text(name, self.snapshot))

    def _run_echo(self, topic_name):
        if is_ros2():
            cmd_str = f"ros2 topic echo {topic_name}"
        else:
            cmd_str = f"rostopic echo {topic_name}"

        self.info_box.setPlainText(f"Launching echo for\n{topic_name}")

        cmds = [
            ["x-terminal-emulator", "-e", "bash", "-lc", cmd_str],
            ["gnome-terminal", "--", "bash", "-lc", cmd_str + "; exec bash"],
            ["xterm", "-e", "bash", "-lc", cmd_str + "; exec bash"],
        ]

        for cmd in cmds:
            try:
                subprocess.Popen(cmd)
                return
            except Exception:
                pass

        self.info_box.setPlainText(
            f"Could not launch terminal.\n\nRun manually:\n{cmd_str}"
        )
    def _hide_item(self, item_kind, name):
        if item_kind == "node":
            self.hidden_nodes.add(name)
        else:
            self.hidden_topics.add(name)
        self.refresh_graph()

    def refresh_graph(self):
        if self._drag_pause_counter > 0:
            self._drag_pause_counter -= 1
            self.status_label.setText("status: drag hold")
            return
        try:
            self.snapshot = GraphSnapshot.from_master()
            self.graph.populate_from_snapshot(
                self.snapshot,
                positions=self.positions,
                filter_text=self.search_edit.text(),
                show_rosout=self.show_rosout_cb.isChecked(),
                show_self=self.show_self_cb.isChecked(),
                show_clock=self.show_clock_cb.isChecked(),
                show_rviz=self.show_rviz_cb.isChecked(),
                show_floating=self.show_floating_cb.isChecked(),
                hidden_nodes=self.hidden_nodes,
                hidden_topics=self.hidden_topics,
                nodes_only=self.nodes_only_cb.isChecked(),
                prune_isolated_topics=self.prune_topics_cb.isChecked(),
                draw_namespaces=self.namespace_cb.isChecked(),
            )
            for name, item in self.graph.node_items.items():
                self.positions[name] = (float(item.pos().x()), float(item.pos().y()))
            for name, item in self.graph.topic_items.items():
                self.positions[name] = (float(item.pos().x()), float(item.pos().y()))
            if self.first_load:
                self._fit_graph()
                self.first_load = False
            self.status_label.setText(
                "status: nodes={} topics={} edges={} hidden={} layout=occupancy".format(
                    len(self.graph.node_items),
                    len(self.graph.topic_items),
                    len(self.graph.edge_items),
                    len(self.hidden_nodes) + len(self.hidden_topics),
                )
            )
        except Exception as exc:
            self.status_label.setText("status: error")
            self.info_box.setPlainText("Failed to read ROS master.\n\n{}\n\n{}".format(str(exc), traceback.format_exc()))
