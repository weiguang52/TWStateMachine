from setuptools import find_packages, setup
from glob import glob
import os
package_name = 'robot_state_machine'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*.launch.py'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='admin',
    maintainer_email='admin@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'main_node=robot_state_machine.main_node_offline:main',
            'out_node=robot_state_machine.out_node:main',
            'mpu_node=robot_state_machine.mpu_node:main',
            'vibration_monitor_node=robot_state_machine.vibration_monitor_node:main',
        ],
    },
)
