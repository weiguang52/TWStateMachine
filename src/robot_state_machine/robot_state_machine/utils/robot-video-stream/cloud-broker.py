import os
import zmq
import sys
from loguru import logger
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import cfg

logger.remove()
logger.add(sys.stderr, format="{time} {level} {message}", level="INFO")

def main():
    context = zmq.Context()

    # Frontend：Receive from Robot
    frontend = context.socket(zmq.XSUB)
    frontend.bind(f"tcp://{cfg['network']['broker_ip']}:{cfg['network']['robot_producer_port']}")

    # Backend：Send to Other Consumers
    backend = context.socket(zmq.XPUB)
    backend.bind(f"tcp://{cfg['network']['broker_ip']}:{cfg['network']['broker_consumer_port']}")

    logger.info("=== Starting Robot Video Broker ===")
    logger.info(f" Listening: {cfg['network']['robot_producer_port']} (Robot In)")
    logger.info(f" Listening: {cfg['network']['broker_consumer_port']} (AI Out)")

    try:
        zmq.proxy(frontend, backend)
    except KeyboardInterrupt:
        logger.info("\nRobot Video Broker stopped.")
    finally:
        frontend.close()
        backend.close()
        context.term()

if __name__ == "__main__":
    main()
