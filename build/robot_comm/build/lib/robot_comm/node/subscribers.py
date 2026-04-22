import time
import sys
import os
import zmq
import importlib
import cv2
import numpy as np
from cv_bridge import CvBridge
from loguru import logger

from rclpy.node import Node
from std_msgs.msg import String
#from audio_msg.msg import SmartAudioData
from std_msgs.msg import UInt8MultiArray
from sensor_msgs.msg import Image
from array import array
from robot_comm.grpc.proto import media_stream_pb2
from robot_comm.grpc.proto import media_stream_pb2_grpc
from robot_comm.config.settings import ZMQ_VIDEO_BROKER_ENDPOINT
from robot_comm.config.settings import ROBOT_ID

# setup logger
logger.add("/tmp/robot_comm.log", rotation="100 MB", level="INFO")

class SubscriberBase:
    def __init__(self, node: Node, topic: str, msg_type, grpc_client):
        self.node = node
        self.topic = topic
        self.grpc_client = grpc_client
        
        # 订阅指定 topic
        self.subscription = node.create_subscription(
            msg_type,
            topic,
            self.callback,
            10
        )

        # TTS publisher
        self.tts_publisher = node.create_publisher(UInt8MultiArray, "/audio_stream", 10)

    def callback(self, msg):
        """Base callback, to be overridden by subclasses"""
        raise NotImplementedError

#
# Subscribers: 
#    1. extreme_sensor
#        - topic: /extreme_sensor
#        - msg_type: ExtremeSensor
#    2. fault_information
#        - topic: /fault_information
#        - msg_type: FaultInformation
#
class ExtremeSensorDataSubscriber(SubscriberBase):
    def __init__(self, node: Node, topic: str, msg_type, grpc_client):
        super().__init__(node, topic, msg_type, grpc_client)

    def callback(self, msg):
        logger.info("Call ExtremeSensorDataSubscriber callback")
        try:
            # 假设 SensorData 包含 value 和 timestamp 字段
            data = f'value: {msg.value}, timestamp: {msg.timestamp}'
            response = self.grpc_client.report_message(self.topic, data)
            logger.info(f'Reported {self.topic} to gRPC: {response.message}')

        except Exception as e:
            logger.error(f'gRPC error for {self.topic}: {str(e)}')
            
#
# 2. Fault Information Subscriber
class FaultInformationSubscriber(SubscriberBase):
    def __init__(self, node: Node, topic: str, msg_type, grpc_client):
        super().__init__(node, topic, msg_type, grpc_client)

    def callback(self, msg):
        logger.info("Call FaultInformationSubscriber callback")
        try:
            response = self.grpc_client.report_message(self.topic, msg.data)
            logger.info(f'Reported {self.topic} to gRPC: {response.message}')
        except Exception as e:
            logger.info(f'gRPC error for {self.topic}: {str(e)}')

#
# 2. Base ZMQ Camera Subscriber
# 
class BaseZMQCameraSubscriber(SubscriberBase):
    def __init__(self, node: Node, topic: str, msg_type, grpc_client, camera_suffix=""):
        super().__init__(node, topic, msg_type, grpc_client)
        self.bridge = CvBridge()
        
        # init ZMQ
        self.zmq_context = zmq.Context().instance() # use shared context
        self.zmq_socket = self.zmq_context.socket(zmq.PUB)
        
        # read config
        logger.info(f"Connecting to ZMQ broker at {ZMQ_VIDEO_BROKER_ENDPOINT}")
        self.zmq_socket.connect(f"tcp://{ZMQ_VIDEO_BROKER_ENDPOINT}")
        self.zmq_socket.setsockopt(zmq.SNDHWM, 2)  # set high water mark
        
        # construct camera topic
        self.zmq_topic = f"robot_{ROBOT_ID}_camera{camera_suffix}".encode('utf-8')
        
        # frame control
        self.target_fps = 5.0
        self.pub_interval = 1.0 / self.target_fps
        self.last_pub_time = 0.0
        
        # image parameters
        self.target_width = 640
        self.target_height = 480
        self.jpeg_quality = 80
    
    def callback(self, msg: Image):
        # control publish rate
        now = time.time()
        if now - self.last_pub_time < self.pub_interval:
            # exceed rate limit, skip this frame
            return
        self.last_pub_time = now
        logger.info("Call BaseZMQCameraSubscriber callback")
        
        # 1. format check
        if msg.encoding != 'bgr8':
            logger.error(f"Unsupported encoding: {msg.encoding}. Expected 'bgr8'.")
            return
    
        # 2. get image data
        try:
            # convert ROS Image to OpenCV image
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

            # resize image
            cv_image = cv2.resize(cv_image, (self.target_width, self.target_height))
            
            # compress to JPEG
            _, compressed_data = cv2.imencode(".jpg", cv_image, [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality])
            image_bytes = compressed_data.tobytes()
            logger.info(f"Prepared image of size: {len(image_bytes)} bytes")
            
            # 3. send via ZMQ
            self.zmq_socket.send_multipart([self.zmq_topic, image_bytes])
            logger.info(f"Published image to ZMQ topic: {self.zmq_topic.decode('utf-8')}")
        except Exception as e:
            logger.error(f"Failed to convert ROS Image to OpenCV image: {e}")
            return

class LeftCameraImageSubscriber(BaseZMQCameraSubscriber):
    def __init__(self, node: Node, topic: str, msg_type, grpc_client):
        super().__init__(node, topic, msg_type, grpc_client, camera_suffix="_left")
        logger.info("Initialized LeftCameraImageSubscriber")

class RightCameraImageSubscriber(BaseZMQCameraSubscriber):
    def __init__(self, node: Node, topic: str, msg_type, grpc_client):
        super().__init__(node, topic, msg_type, grpc_client, camera_suffix="_right")
        logger.info("Initialized RightCameraImageSubscriber")

class AudioSmartSubscriber(SubscriberBase):
    def __init__(self, node, topic, msg_type, grpc_client):
        super().__init__(node, topic, msg_type, grpc_client)

    def callback(self, msg):
        # TODO: call grpc client
        print("Get Audio Smart data.")
        
class AudioASRSubscriber(SubscriberBase):
    def __init__(self, node, topic, msg_type, grpc_client):
        super().__init__(node, topic, msg_type, grpc_client)
        
    def callback(self, msg):
        # TODO: call grpc client
        logger.info(f"Get Audio ASR msg: {msg}")
        responses = self.grpc_client.request_audio(msg.data)

        logger.info("Parsing response stream")
        for res in responses:
            if res.type == media_stream_pb2.AUDIO:  # 只取 TTS 音频分片
                logger.info(f"Received TTS chunk, size={len(res.audio_chunk)} bytes")
                audio_msg = UInt8MultiArray()
                audio_msg.data = list(res.audio_chunk)  # 每个字节是 int (0~255)
                self.do_publish_voice(audio_msg)
                logger.info("Published TTS chunk to /audio_stream")
            elif res.type == media_stream_pb2.TRANSCRIPT:
                logger.info(f"Received transcript: {res.transcript}")
            elif res.type == media_stream_pb2.ACTION:
                logger.info(f"Received action data, size={len(res.action_npz)} bytes")
                action_data = res.action_npz
                action_description = res.action_description
                self.do_action(action_data)
            elif res.type == media_stream_pb2.ERROR:
                logger.info(f"Error from server: {res.error_msg}")
            else:
                logger.warning(f"Unknown response type: {res.type}")

    def do_action(self, action_data: bytes):
        final_path = "/tmp/robot_action.npy"
        tmp_path = final_path + ".tmp"

        # ✅ 关键：空动作直接丢弃，不写文件
        if not action_data:
            return

        # ✅ 原子写入：先写 tmp，再 replace
        with open(tmp_path, "wb") as f:
            f.write(action_data)
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp_path, final_path)



    def do_publish_voice(self, voice):
        # publish voice data
        self.tts_publisher.publish(voice)

def create_subscribers(node: Node, topics: dict, grpc_client):
    """Create subscribers for specified topics"""
    subscribers = []
    msg_module = importlib.import_module('robot_msg.msg')
    for topic_name, msg_type_str in topics.items():
        if topic_name == "sensor_data":
            msg_type = getattr(msg_module, msg_type_str)
            subscriber = ExtremeSensorDataSubscriber(node, topic_name, msg_type, grpc_client)
            logger.info(f"subscribe to : {topic_name}")
        elif topic_name == "fault_information":
            msg_type = getattr(msg_module, msg_type_str)
            subscriber = FaultInformationSubscriber(node, topic_name, msg_type, grpc_client)
            logger.info(f"subscribe to : {topic_name}")
        elif topic_name == "audio_smart":
            subscriber = AudioSmartSubscriber(node, topic_name, SmartAudioData, grpc_client)
            logger.info(f"subscribe to: {topic_name}")
        elif topic_name == "audio_asr":
            subscriber = AudioASRSubscriber(node, topic_name, String, grpc_client)
            logger.info(f"subscribe to : {topic_name}")
        elif topic_name == "/camera/left/image_bgr8":
            subscriber = LeftCameraImageSubscriber(node, topic_name, Image, grpc_client)
            logger.info(f"subscribe to: {topic_name}")
        elif topic_name == "/camera/right/image_bgr8":
            subscriber = RightCameraImageSubscriber(node, topic_name, Image, grpc_client)
            logger.info(f"subscribe to: {topic_name}")
        else:
            # Default subscriber for unknown topics
            subscriber = SubscriberBase(node, topic_name, String, grpc_client)
        
        if 'subscriber' in locals():
            subscribers.append(subscriber)
            logger.info(f"Created subscriber for topic: {topic_name}")
    
    # return _full_create_subscribers_logic(node, topics, grpc_client, msg_module)
    return subscribers

def _full_create_subscribers_logic(node: Node, topics: dict, grpc_client, msg_module):
    """Create subscribers for all topics (for testing)"""
    subscribers = []
    
    for topic_name, msg_type_str in topics.items():
        if topic_name == "sensor_data":
            msg_type = getattr(msg_module, msg_type_str)
            subscriber = ExtremeSensorDataSubscriber(node, topic_name, msg_type, grpc_client)
            logger.info(f"subscribe to : {topic_name}")
        elif topic_name == "fault_information":
            msg_type = getattr(msg_module, msg_type_str)
            subscriber = FaultInformationSubscriber(node, topic_name, msg_type, grpc_client)
            logger.info(f"subscribe to : {topic_name}")
        elif topic_name == "audio_smart":
            subscriber = AudioSmartSubscriber(node, topic_name, SmartAudioData, grpc_client)
            logger.info(f"subscribe to: {topic_name}")
        elif topic_name == "audio_asr":
            subscriber = AudioASRSubscriber(node, topic_name, String, grpc_client)
            logger.info(f"subscribe to : {topic_name}")
        elif topic_name == "/camera/left/image_bgr8":
            subscriber = LeftCameraImageSubscriber(node, topic_name, Image, grpc_client)
            logger.info(f"subscribe to: {topic_name}")
        elif topic_name == "/camera/right/image_bgr8":
            subscriber = RightCameraImageSubscriber(node, topic_name, Image, grpc_client)
            logger.info(f"subscribe to: {topic_name}")
        else:
            # Default subscriber for unknown topics
            subscriber = SubscriberBase(node, topic_name, String, grpc_client)

        if subscriber:
            subscribers.append(subscriber)
            logger.info(f"Created subscriber for topic: {topic_name}")

    return subscribers
    