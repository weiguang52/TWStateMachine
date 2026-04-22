import cv2
import zmq
import numpy as np
from loguru import logger
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import cfg

logger.remove()
logger.add(lambda msg: print(msg, end=''), format="{time} {level} {message}", level="INFO")

def main():
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    
    # [修改点] 连接本地 Broker 输出端
    logger.info("AI is connecting to local broker...")
    socket.connect(f"tcp://{cfg['network']['broker_ip']}:{cfg['network']['broker_consumer_port']}")
    
    # 订阅所有
    socket.setsockopt_string(zmq.SUBSCRIBE, "")
    
    # [关键] 只取最新一帧
    socket.setsockopt(zmq.RCVHWM, 1)
    socket.setsockopt(zmq.CONFLATE, 1)

    window_name = "Localhost Stream"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

    while True:
        try:
            topic, frame_data = socket.recv_multipart()
            
            # 解码
            np_arr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if frame is not None:
                cv2.imshow(window_name, frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except KeyboardInterrupt:
            break

    cv2.destroyAllWindows()
    context.term()

if __name__ == "__main__":
    main()
