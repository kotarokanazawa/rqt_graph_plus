cmake_minimum_required(VERSION 3.0.2)
project(rqt_graph_plus_ros1)

find_package(catkin REQUIRED COMPONENTS
  rospy
  rosgraph
  rosnode
  python_qt_binding
  qt_gui
  rqt_gui
  rqt_gui_py
)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/rqt_graph_plus
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY
  src/rqt_graph_plus
  DESTINATION ${CATKIN_PACKAGE_PYTHON_DESTINATION}
)

install(FILES
  plugin.xml
  package.xml
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
