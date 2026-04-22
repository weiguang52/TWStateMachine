import grpc
import time
import uuid
from loguru import logger
from robot_comm.grpc.proto import media_stream_pb2
from robot_comm.grpc.proto import media_stream_pb2_grpc

class RobotCommGrpcClient:
    def __init__(self, channel: grpc.Channel):
        self.channel = channel
        #self.stub = robot_comm_pb2_grpc.RobotCommStub(self.channel)
        # Initilize the gRPC stub
        self.stub = media_stream_pb2_grpc.VoiceAgentStub(self.channel)
        logger.info("gRPC client inited.")

    #def report_message(self, topic, data):
    #    logger.info(f'Reporting message to topic {topic}')
    #    request = robot_comm_pb2.ReportRequest(topic=topic, data=data)
    #    return self.stub.ReportMessage(request)
    
    def request_audio(self, text):
        logger.info(f'Requesting audio for text {text}')
        session_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())
        
        def generate_request():
            # first message: send meta data
            yield media_stream_pb2.AudioRequest(
                session_id  = session_id,
                robot_id    = "robot_test",
                request_id  = request_id,
                ts          = int(time.time()*1000),
                meta        = {"text" : text}
            )

            # second message: notification of end
            yield media_stream_pb2.AudioRequest(
                session_id  = session_id,
                robot_id    = "robot_test",
                request_id  = request_id,
                end_of_stream   = True
            )

        return self.stub.StreamSession(generate_request())

    def set_model_preference(self, llm_model : str) -> bool:
        """Set Robot side model preference
        Args:
            llm_model (str): llm model name
        Returns:
            bool: True if success, False otherwise
        """
        
        logger.info(f'Setting model preference to {llm_model}')
        session_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())
        ts = int(time.time())
        
        request = media_stream_pb2.ModelPreferenceRequest(
            session_id = session_id,
            robot_id = "robot_test",
            request_id = request_id,
            ts = ts,
            llm_model = llm_model)
        
        response = self.stub.SetModelPreference(request)
        
        # if error_msg exist, return False
        if response.error_msg:
            return False
        
        return True
    
    def upload_image(self, image_data : bytes, camera : str) -> bool:
        """Upload image from Robot to Cloud
        Args:
            image_data (bytes): image data
        Returns:
            bool: True if success, False otherwise
        """
        logger.info(f'Uploading image to cloud')
        
        session_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())
        ts = int(time.time())
        filename = camera
        
        request = media_stream_pb2.ImageUploadRequest(
            session_id = session_id,
            robot_id = "robot_test",
            request_id = request_id,
            ts = ts,
            filename = filename,
            mime_type = "image/jpg",
            image_data = image_data,
            meta = {}
        )

        response = self.stub.UploadImage(request)
        
        # if error_msg exist, return False
        if response.error_msg:
            return False

        return True

    def __del__(self):
        logger.info("gRPC client deleted.")
