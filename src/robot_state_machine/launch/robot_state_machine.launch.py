from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='robot_state_machine',
            executable='/home/sunrise/miniconda3/envs/TWStateMachine/bin/python',
            arguments=['/home/sunrise/TWStateMachine/src/robot_state_machine/robot_state_machine/main_node_online_v2.py'],
            name='main_node',
            output='screen',
        ),
        Node(
            package='robot_state_machine',
            executable='/home/sunrise/miniconda3/envs/TWStateMachine/bin/python',
            arguments=['/home/sunrise/TWStateMachine/src/robot_state_machine/robot_state_machine/out_node.py'],
            name='out_node',
            output='screen',
        ),
        Node(
            package='robot_state_machine',
            executable='/home/sunrise/miniconda3/envs/TWStateMachine/bin/python',
            arguments=['/home/sunrise/TWStateMachine/src/robot_state_machine/robot_state_machine/utils/admittance_calculate.py'],
            name='send_node',
            output='screen',
        ),
        # Node(
        #     package='robot_state_machine',
        #     executable='/home/sunrise/miniconda3/envs/TWStateMachine/bin/python',
        #     arguments=['/home/sunrise/TWStateMachine/src/robot_state_machine/robot_state_machine/mpu_read_parse.py'],
        #     name='mpu_node',
        #     output='screen',
        # ),
        # Node(
        #     package='robot_state_machine',
        #     executable='/home/sunrise/miniconda3/envs/TWStateMachine/bin/python',
        #     arguments=['/home/sunrise/TWStateMachine/src/robot_state_machine/robot_state_machine/imu_vibration_monitor.py'],
        #     name='vibration_monitor_node',
        #     output='screen',
        # ),
    ])
