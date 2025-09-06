import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
OWNER_NICKNAME = os.getenv('OWNER_NICKNAME', 'Nobody')

DATA_FOLDER = Path("/app/data") if os.path.exists("/app/data") else Path(".")
DATA_FOLDER.mkdir(exist_ok=True)

SUDO_USERS_FILE = DATA_FOLDER / "SUDOUsers.json"
RESTART_TIME_FILE = DATA_FOLDER / "restart_time.txt"
LOCK_FILE = "modubot.lock"
CONSOLE_LOGO_FILE = Path("ConsoleLogo.txt")

MODULES_FOLDER = DATA_FOLDER / "ModuBotModules"
MODULES_FOLDER.mkdir(exist_ok=True)

GITHUB_RAW_URL_APP = "https://raw.githubusercontent.com/BrokenByteOfCode/ModuBot/main/app.py"
MODULES_REPO_URL = "https://api.github.com/repos/BrokenByteOfCode/ModuBotModules/contents"
