import rclpy
import grpc
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from robot_comm.node.subscribers import create_subscribers
from robot_comm.node.cloud_service import CloudService
from robot_comm.grpc.client import RobotCommGrpcClient
from robot_comm.config.settings import TOPICS, GRPC_SERVER
from loguru import logger

logger.add("/tmp/robot_comm.log")

class RobotCommNode(Node):
    def __init__(self):
        logger.info("Initializing RobotCommNode")
        super().__init__('robot_comm_node')
        # Create gRPC client
        self.grpc_channel = grpc.insecure_channel(GRPC_SERVER)
        self.grpc_client = RobotCommGrpcClient(self.grpc_channel)

        # Create ROS2 node
        logger.info(f"Creating subscribers")
        self.subscribers = create_subscribers(self, TOPICS, self.grpc_client)

def main(args=None):
    logger.info("Starting RobotComm")
    rclpy.init(args=args)
    node = RobotCommNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        node.logger.info('Shutting down')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
