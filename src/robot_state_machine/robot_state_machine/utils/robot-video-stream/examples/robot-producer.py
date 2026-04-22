import os
import cv2
import zmq
import time
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import cfg
from loguru import logger
logger.remove()
logger.add(lambda msg: print(msg, end=''), format="{time} {level} {message}", level="INFO")

def main():
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    
    # Connect to Broker
    logger.info("Robot is connecting to local broker...")
    socket.connect(f"tcp://{cfg['network']['broker_ip']}:{cfg['network']['robot_producer_port']}")
    
    # Set high water mark to avoid piling up messages
    socket.setsockopt(zmq.SNDHWM, 2)

    cap = cv2.VideoCapture(0)
    # Reduce resolution for faster processing
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1080)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    frame_count = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Print a timestamp to help observe latency
            cv2.putText(frame, str(frame_count), (50, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            # Encode JPEG
            _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            
            # Send frame with topic "robot_local"
            socket.send_multipart([b"robot_local", buffer])
            
            logger.info(f"Pushed frame: {frame_count}")
            frame_count += 1
            
            # Simulate 5 FPS (can run faster locally)
            time.sleep(0.2)
            
    except KeyboardInterrupt:
        logger.info("\nRobot video stream stopped.")
    finally:
        cap.release()
        context.term()

if __name__ == "__main__":
    main()