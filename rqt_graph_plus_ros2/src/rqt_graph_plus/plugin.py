from rqt_gui_py.plugin import Plugin
from .main_widget import MainWidget

class GraphPlus(Plugin):
    def __init__(self, context):
        super(GraphPlus, self).__init__(context)
        self.setObjectName('GraphPlus')
        self._widget = MainWidget()
        context.add_widget(self._widget)
