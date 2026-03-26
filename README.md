# rqt_graph_plus multi-ROS

ROS1 と ROS2 を同じ zip にまとめた版です。  
中には次の2パッケージが入っています。

- `rqt_graph_plus_ros1`
- `rqt_graph_plus_ros2`

## 置き方

この zip を **workspace の `src/` に展開**します。

```bash
cd ~/ws/src
unzip rqt_graph_plus_multi_ros.zip
```

展開後の構成:

```text
src/
  rqt_graph_plus_multi_ros/
    rqt_graph_plus_ros1/
    rqt_graph_plus_ros2/
    build_rqt_graph_plus.sh
    run_rqt_graph_plus.sh
```

## いちばん簡単な使い方

### ROS1
```bash
source /opt/ros/noetic/setup.bash
cd ~/imax_ws/src/rqt_graph_plus_multi_ros
./build_rqt_graph_plus.sh
./run_rqt_graph_plus.sh
```

### ROS2
```bash
source /opt/ros/humble/setup.bash
cd ~/ws/src/rqt_graph_plus_multi_ros
./build_rqt_graph_plus.sh
./run_rqt_graph_plus.sh
```

## 手動でビルドする場合

### ROS1
```bash
source /opt/ros/noetic/setup.bash
cd ~/imax_ws
catkin build rqt_graph_plus_ros1
source devel/setup.bash
rosrun rqt_graph_plus_ros1 rqt_graph_plus
```

### ROS2
```bash
source /opt/ros/humble/setup.bash
cd ~/ws
colcon build --packages-select rqt_graph_plus_ros2 --symlink-install
source install/setup.bash
ros2 run rqt_graph_plus_ros2 rqt_graph_plus
```

## メモ

- 自動切替は `ROS_VERSION` を見て行います。
- ROS1/ROS2 でビルドツールの仕様が違うため、**完全に1つの package.xml にはしていません**。
- その代わり、**1つの zip / 1つの共通コード系統 / 2つの薄い wrapper package** にしています。
