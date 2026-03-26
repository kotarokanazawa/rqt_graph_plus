#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if [ "${ROS_VERSION}" = "2" ]; then
  echo "[rqt_graph_plus] ROS2 build"

  colcon build \
    --base-paths "${WORKSPACE_DIR}/src" \
    --build-base "${WORKSPACE_DIR}/build" \
    --install-base "${WORKSPACE_DIR}/install" \
    --packages-select rqt_graph_plus_ros2 \
    --symlink-install

elif [ "${ROS_VERSION}" = "1" ]; then
  echo "[rqt_graph_plus] ROS1 build"

  cd "${WORKSPACE_DIR}"
  if command -v catkin >/dev/null 2>&1; then
    catkin build rqt_graph_plus_ros1 --workspace "${WORKSPACE_DIR}"
  else
    catkin_make --source "${WORKSPACE_DIR}/src" --pkg rqt_graph_plus_ros1
  fi

else
  echo "ROS_VERSION is not set to 1 or 2."
  echo "Please source your ROS environment first."
  exit 1
fi
