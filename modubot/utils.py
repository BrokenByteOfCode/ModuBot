import os
import json
import logging
import time
from . import config

logger = logging.getLogger(__name__)

def load_sudo_users():
    try:
        if os.path.exists(config.SUDO_USERS_FILE):
            with open(config.SUDO_USERS_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error reading {config.SUDO_USERS_FILE}: {e}")
    return []

def save_sudo_users(sudo_users):
    try:
        with open(config.SUDO_USERS_FILE, "w", encoding="utf-8") as file:
            json.dump(sudo_users, file, indent=4)
        return True
    except IOError as e:
        logger.error(f"Error writing to {config.SUDO_USERS_FILE}: {e}")
        return False

def handle_restart_notification(app):
    if os.path.exists(config.RESTART_TIME_FILE):
        try:
            with open(config.RESTART_TIME_FILE, 'r') as f:
                lines = f.readlines()
                if len(lines) >= 3:
                    restart_time = float(lines[0].strip())
                    chat_id = int(lines[1].strip())
                    message_id = int(lines[2].strip())
                    
                    restart_duration = time.time() - restart_time
                    try:
                        app.edit_message_text(
                            chat_id, message_id, 
                            f"✅ Bot restarted successfully in {restart_duration:.2f}s"
                        )
                    except Exception:
                        pass
            os.remove(config.RESTART_TIME_FILE)
        except Exception as e:
            logger.error(f"Error handling restart notification: {e}")