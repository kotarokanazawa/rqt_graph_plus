from setuptools import setup

package_name = 'rqt_graph_plus_ros2'
module_name = 'rqt_graph_plus'

setup(
    name=package_name,
    version='1.0.0',
    packages=[module_name],
    package_dir={'': 'src'},
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml', 'plugin.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='user',
    maintainer_email='user@todo.com',
    description='Enhanced ROS graph viewer for ROS2.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'rqt_graph_plus = rqt_graph_plus.cli:main',
        ],
    },
)