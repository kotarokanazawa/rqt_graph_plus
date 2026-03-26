#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if [ "${ROS_VERSION}" = "2" ]; then
  echo "[rqt_graph_plus] ROS2 run"
  source /opt/ros/humble/setup.bash
  source "${WORKSPACE_DIR}/install/setup.bash"
  ros2 run rqt_graph_plus_ros2 rqt_graph_plus --force-discover

elif [ "${ROS_VERSION}" = "1" ]; then
  echo "[rqt_graph_plus] ROS1 run"
  source /opt/ros/noetic/setup.bash
  source "${WORKSPACE_DIR}/devel/setup.bash"
  rosrun rqt_graph_plus_ros1 rqt_graph_plus

else
  echo "ROS_VERSION is not set to 1 or 2."
  exit 1
fi