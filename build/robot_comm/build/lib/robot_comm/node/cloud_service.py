import json
import os
from loguru import logger
from rclpy.node import Node
from std_msgs.msg import String
from robot_msg.srv import CloudCommand

class CloudService(Node):
    def __init__(self, grpc_client):
        super().__init__('CloudService')
        self.services = self.create_service(CloudCommand, 'cloud_command', self.handle_cloud_command)
        self.grpc_client = grpc_client
    
    def handle_cloud_command(self, request, response):
        logger.info(f"Received command for {request.target_service}")
        try:
            # parse request
            target_service  = request.target_service
            payload_json    = json.loads(request.payload_json)
            logger.info(f"Received command for {request.target_service} with payload {payload_json}")
            
            if target_service == "set_llm_model":
                # parse payload
                model_name = payload_json.get("model_name")
                logger.info(f"Setting model_name to {model_name}")

                if model_name == None:
                    logger.error(f"Missing model_name in payload")
                    response.error_msg = "Missing model_name in payload"
                    return response

                # call rpc
                response = self.rpc_set_llm_model(model_name)
                return response

            elif target_service == "upload_image":
                # parse payload
                image_path = payload_json.get("image_path")
                logger.info(f"Uploading image from {image_path}")
                
                # check if image exists
                if not os.path.exists(image_path):
                    logger.error(f"Image not exists")
                    response.error_msg = "Image not exists"
                    return response
                
                respone = self.rpc_upload_image(image_path)
                return respone 
        except Exception as e:
            logger.error(f"Error in handle_cloud_command: {str(e)}")
            response.error_msg = str(e)
            return response

    def rpc_set_llm_model(self, model_name):
        logger.info(f"Calling set LLM model rpc")
        response = "failed"
        res = self.grpc_client.set_model_preference(model_name)
        if res:
            response = "success"

        return response

    def rpc_upload_image(self, image_path):
        logger.info(f"Calling upload image rpc")
        response = "failed"
        res = self.grpc_client.upload_image(image_path)
        if res:
            response = "success"

        return response
