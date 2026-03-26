# rqt_graph_plus

Enhanced rqt_graph for both ROS1 and ROS2

---

## Installation

### Directory Structure
```text
your_ws/
  src/
    rqt_graph_plus/
      rqt_graph_plus_ros1/
      rqt_graph_plus_ros2/
      build_rqt_graph_plus.sh
      run_rqt_graph_plus.sh
```

---

### Common Steps (ROS1 / ROS2)

```bash
source /opt/ros/<your_ros>/setup.bash
cd ~/your_ws/src
git clone this repository
cd rqt_graph_plus
./build_rqt_graph_plus.sh
./run_rqt_graph_plus.sh
```

* noetic (ROS1)
* humble (ROS2)

---

## Alias (Recommended)

```bash
echo 'alias rqt_graph_plus="cd ~/your_ws/src/rqt_graph_plus && ./run_rqt_graph_plus.sh"' >> ~/.bashrc
source ~/.bashrc
```

Then simply run:

```bash
rqt_graph_plus
```

---

## Controls

* Left Click  
  Select node / topic (connected elements are highlighted)

* Double Click  
  Zoom to highlighted nodes / topics

* Drag  
  Move node / topic

* Drag namespace box  
  Move grouped elements together

* Middle Click  
  Pan view

* Mouse Wheel  
  Zoom in / out

* Right Click  
  Info / Echo / Hide

---

## Features

* Real-time communication graph visualization
* Node-only mode (with direction indicators)

  * ● publisher / ○ subscriber
* Namespace grouping and batch manipulation
* Display filters

  * `/clock`
  * `/rosout`
  * rviz-related
  * floating nodes
* Automatic layout (no overlap)
* Manual layout persistence

