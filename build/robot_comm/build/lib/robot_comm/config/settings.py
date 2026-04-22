# Define the topic names and message type
# {"topic_nam" : "msg_type"}
TOPICS = {
    #"sensor_data": "ExtremeSensorAlert",
    #"fault_information": "FaultInformation",
    #"audio_smart" : "audio_msg.msg.SmartAudioData",
    "audio_asr" : "std_msgs.msg.String",
    "/camera/left/image_bgr8" : "sensor_msgs/msg/Image",
    "/camera/right/image_bgr8" : "sensor_msgs/msg/Image",
}

GRPC_SERVER = "36.103.199.58:50051"

ZMQ_VIDEO_BROKER_ENDPOINT = "36.103.199.58:5555"

ROBOT_ID = "robot_001"
