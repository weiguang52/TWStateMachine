import yaml
import os
import sys
from loguru import logger

def load_config():
    """
    Load the config.yaml file located in the project root directory.
    Returns the configuration as a dictionary.
    """
    # Get the absolute path of the current script (utils/config.py)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Go up one level to find the project root directory (robot-video-stream/)
    project_root = os.path.dirname(current_dir)
    
    config_path = os.path.join(project_root, 'config.yaml')

    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)

    with open(config_path, 'r', encoding='utf-8') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.error(f"Config file format error: {e}")
            sys.exit(1)

# Preload configuration, other files can import this variable directly
cfg = load_config()
