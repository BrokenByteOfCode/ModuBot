import logging
import os
import sys
import psutil
from modubot.bot import ModuBot
from modubot import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    if os.path.exists(config.LOCK_FILE):
        try:
            with open(config.LOCK_FILE, 'r') as f:
                pid = int(f.read())
            if psutil.pid_exists(pid):
                logger.error(f"Another instance is running with PID {pid}. Exiting.")
                sys.exit(1)
        except (IOError, ValueError):
            logger.warning("Corrupted lock file found. Removing.")

    try:
        with open(config.LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
            
        bot = ModuBot()
        bot.run()
        
    finally:
        if os.path.exists(config.LOCK_FILE):
            os.remove(config.LOCK_FILE)
        logger.info("ModuBot stopped. Lock file removed.")

if __name__ == "__main__":
    main()