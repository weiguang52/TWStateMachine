import grpc
from concurrent import futures
import time
import uuid
import logging
import threading

# 导入生成的gRPC代码
import voice_agent_pb2
import voice_agent_pb2_grpc

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceAgentServicer(voice_agent_pb2_grpc.VoiceAgentServicer):
    def __init__(self):
        self.sessions = {}  # 存储会话信息
        
    def StreamSession(self, request_iterator, context):
        """双向流RPC：处理音频流"""
        logger.info("StreamSession started")
        
        try:
            for request in request_iterator:
                logger.info(f"Received audio chunk from session: {request.session_id}, "
                           f"request_id: {request.request_id}, "
                           f"chunk_size: {len(request.audio_chunk)}")
                
                # 模拟ASR处理 - 返回转录文本
                if len(request.audio_chunk) > 0:
                    transcript_response = voice_agent_pb2.AudioResponse(
                        request_id=request.request_id,
                        ts=int(time.time() * 1000),
                        type=voice_agent_pb2.ResponseType.TRANSCRIPT,
                        transcript=f"Transcribed text for request {request.request_id}",
                        model_version="asr-v1.0"
                    )
                    yield transcript_response
                
                # 模拟TTS处理 - 返回音频数据
                if request.end_of_stream:
                    # 模拟生成TTS音频分片
                    for i in range(3):  # 发送3个音频分片
                        audio_response = voice_agent_pb2.AudioResponse(
                            request_id=request.request_id,
                            ts=int(time.time() * 1000),
                            type=voice_agent_pb2.ResponseType.AUDIO,
                            audio_chunk=f"fake_tts_audio_chunk_{i}".encode(),
                            model_version="tts-v1.0"
                        )
                        yield audio_response
                        time.sleep(0.1)  # 模拟处理延迟
                    
                    # 发送结束标志
                    end_response = voice_agent_pb2.AudioResponse(
                        request_id=request.request_id,
                        ts=int(time.time() * 1000),
                        type=voice_agent_pb2.ResponseType.TRANSCRIPT,
                        transcript="Session completed",
                        end_of_response=True,
                        model_version="system-v1.0"
                    )
                    yield end_response
                    break
                    
        except Exception as e:
            logger.error(f"Error in StreamSession: {e}")
            error_response = voice_agent_pb2.AudioResponse(
                request_id="unknown",
                ts=int(time.time() * 1000),
                type=voice_agent_pb2.ResponseType.ERROR,
                error_msg=str(e),
                end_of_response=True
            )
            yield error_response

    def ProcessAudioUnary(self, request, context):
        """一元RPC：处理单个音频文件"""
        logger.info(f"ProcessAudioUnary called for session: {request.session_id}")
        
        try:
            # 模拟音频处理
            time.sleep(0.5)  # 模拟处理时间
            
            response = voice_agent_pb2.AudioUnaryResponse(
                request_id=request.request_id,
                transcript=f"Unary transcription for {request.request_id}",
                audio=b"fake_tts_response_audio_data",
                model_version="unified-v1.0"
            )
            return response
            
        except Exception as e:
            logger.error(f"Error in ProcessAudioUnary: {e}")
            return voice_agent_pb2.AudioUnaryResponse(
                request_id=request.request_id,
                error_msg=str(e)
            )

    def SetModelPreference(self, request, context):
        """设置模型偏好"""
        logger.info(f"SetModelPreference called: {request.llm_model}")
        
        try:
            # 模拟模型设置
            accepted_models = ["gpt-4", "claude-3", "llama-2"]
            
            if request.llm_model in accepted_models:
                response = voice_agent_pb2.ModelPreferenceResponse(
                    request_id=request.request_id,
                    accepted_model=request.llm_model,
                    model_version=f"{request.llm_model}-v1.0"
                )
                # 添加模型能力信息
                response.model_caps["max_tokens"] = "4096"
                response.model_caps["supports_images"] = "true"
                response.model_caps["max_concurrent"] = "10"
            else:
                response = voice_agent_pb2.ModelPreferenceResponse(
                    request_id=request.request_id,
                    error_msg=f"Model {request.llm_model} not available"
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in SetModelPreference: {e}")
            return voice_agent_pb2.ModelPreferenceResponse(
                request_id=request.request_id,
                error_msg=str(e)
            )

    def UploadImage(self, request, context):
        """上传图片"""
        logger.info(f"UploadImage called: {request.filename}, size: {len(request.image_data)}")
        
        try:
            # 模拟图片处理
            image_id = str(uuid.uuid4())
            
            response = voice_agent_pb2.ImageUploadResponse(
                request_id=request.request_id,
                image_id=image_id,
                width=1024,  # 模拟解析出的宽度
                height=768,  # 模拟解析出的高度
                storage_url=f"https://storage.example.com/images/{image_id}"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in UploadImage: {e}")
            return voice_agent_pb2.ImageUploadResponse(
                request_id=request.request_id,
                error_msg=str(e)
            )

def serve():
    # 创建gRPC服务器
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # 添加服务
    voice_agent_pb2_grpc.add_VoiceAgentServicer_to_server(
        VoiceAgentServicer(), server
    )
    
    # 监听端口
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)
    
    # 启动服务器
    server.start()
    logger.info(f"Server started, listening on {listen_addr}")
    
    try:
        while True:
            time.sleep(86400)  # 保持服务器运行
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        server.stop(0)

if __name__ == '__main__':
    serve()
