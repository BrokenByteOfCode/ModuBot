import logging
import os
import sys
import shutil
import tempfile
from datetime import datetime
import requests
from . import config

logger = logging.getLogger(__name__)

class Updater:
    def __init__(self, app):
        self.app = app

    def get_remote_last_modified(self):
        try:
            response = requests.head(config.GITHUB_RAW_URL_APP, timeout=10)
            if response.status_code == 200 and 'last-modified' in response.headers:
                last_modified = response.headers['last-modified']
                return datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S %Z')
        except Exception as e:
            logger.error(f"Error getting remote last modified: {e}")
        return None

    def get_local_last_modified(self):
        try:
            stat = os.stat(__file__)
            return datetime.fromtimestamp(stat.st_mtime)
        except Exception as e:
            logger.error(f"Error getting local last modified: {e}")
        return None

    def check_for_updates(self):
        remote_time = self.get_remote_last_modified()
        local_time = self.get_local_last_modified()
        
        if not remote_time or not local_time:
            return False
            
        return remote_time > local_time

    def apply_main_update(self):
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, 'app.py')
        try:
            response = requests.get(config.GITHUB_RAW_URL_APP, timeout=10)
            if response.status_code == 200:
                with open(temp_file_path, 'w', encoding='utf-8') as temp_file:
                    temp_file.write(response.text)
                shutil.copy2(temp_file_path, __file__)
                logger.info("Main script updated. Restarting...")
                os.execl(sys.executable, sys.executable, *sys.argv)
        except Exception as e:
            logger.error(f"Error applying main update: {e}")
        finally:
            shutil.rmtree(temp_dir)