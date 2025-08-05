import logging
import os
import sys
import json
import subprocess
import time
import threading
import shutil
import tempfile
import importlib.util
import traceback
from datetime import datetime
from pathlib import Path

import requests
import psutil
import platform
from pyrogram import Client, filters, handlers
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModuBot:
    def __init__(self):
        self.SUDO_USERS_FILE = "SUDOUsers.json"
        self.RESTART_TIME_FILE = "restart_time.txt"
        self.MODULES_FOLDER = Path("ModuBotModules")
        self.GITHUB_RAW_URL = "https://raw.githubusercontent.com/BrokenByteOfCode/ModuBot/main/app.py"
        self.MODULES_REPO_URL = "https://api.github.com/repos/BrokenByteOfCode/ModuBotModules/contents"
        self.CHECK_INTERVAL = 300
        
        self.app = None
        self.owner_nickname = None
        self.bot_firstname = None
        self.sudo_users = []
        self.last_restart_time = datetime.now().strftime("%Y/%d/%m(%B) %H:%M:%S")

        self.loaded_modules = {}
        self.module_handlers = {}
        
        self.MODULES_FOLDER.mkdir(exist_ok=True)

    def fill_console_with_background(self, color_code):
        background = f'\033[{color_code}m'
        clear_screen = '\033[2J'
        move_cursor_top_left = '\033[H'
        print(background + clear_screen + move_cursor_top_left, end='')

    def display_logo(self):
        try:
            self.fill_console_with_background('44')
            logo_path = Path('ConsoleLogo.txt')
            if logo_path.exists():
                with open(logo_path, 'r', encoding='utf-8') as f:
                    logo = f.read()
                
                console_width, console_height = shutil.get_terminal_size((80, 20))
                logo_lines = logo.split('\n')
                logo_height = len(logo_lines)
                logo_width = max(len(line) for line in logo_lines) if logo_lines else 0
                start_y = max((console_height - logo_height) // 2, 0)
                start_x = max((console_width - logo_width) // 2, 0)

                print('\n' * start_y, end='')
                for line in logo_lines:
                    print(' ' * start_x + line)
                    time.sleep(0.1)
                print('\033[0m', end='')
                time.sleep(2)
        except Exception as e:
            logger.error(f"Error displaying logo: {e}")

    def out_of_box_experience(self):
        self.fill_console_with_background('12')
        console_width, console_height = shutil.get_terminal_size((80, 20))
        
        welcome_text = "Welcome to ModuBot!"
        data_prompt = "Enter the required data: {API_ID, API_HASH, OWNER_NICKNAME}"
        hint_text = "You can find {API_ID, API_HASH} at `https://my.telegram.org/`."
        
        welcome_y = max((console_height - 5) // 2 - 1, 0)
        data_prompt_y = welcome_y + 1
        hint_y = max((console_height + 2) // 2 + 1, 0)

        print('\n' * welcome_y + ' ' * ((console_width - len(welcome_text)) // 2) + welcome_text)
        print(' ' * ((console_width - len(data_prompt)) // 2) + data_prompt)
        print('\n' * (hint_y - data_prompt_y - 1), end='')
        print(' ' * ((console_width - len(hint_text)) // 2) + hint_text)
        
        api_id = input(' ' * ((console_width - 10) // 2) + "API_ID: ")
        api_hash = input(' ' * ((console_width - 12) // 2) + "API_HASH: ")
        owner_nickname = input(' ' * ((console_width - 18) // 2) + "OWNER_NICKNAME: ")

        with open('.env', 'w') as env_file:
            env_file.write(f"API_ID={api_id}\nAPI_HASH={api_hash}\nOWNER_NICKNAME={owner_nickname}\n")

    def load_sudo_users(self):
        try:
            if os.path.exists(self.SUDO_USERS_FILE):
                with open(self.SUDO_USERS_FILE, "r", encoding="utf-8") as file:
                    self.sudo_users = json.load(file)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error reading {self.SUDO_USERS_FILE}: {e}")
            self.sudo_users = []

    def save_sudo_user(self, user_id):
        if user_id not in self.sudo_users:
            self.sudo_users.append(user_id)
            try:
                with open(self.SUDO_USERS_FILE, "w", encoding="utf-8") as file:
                    json.dump(self.sudo_users, file)
                logger.info(f"Added user {user_id} to SUDO users.")
            except IOError as e:
                logger.error(f"Error writing to {self.SUDO_USERS_FILE}: {e}")

    def install_module_requirements(self, module_path):
        reqs_file = module_path / "reqs.txt"
        if reqs_file.exists():
            try:
                with open(reqs_file, 'r', encoding='utf-8') as f:
                    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                
                if requirements:
                    logger.info(f"Installing/updating requirements for {module_path.name}")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "-U"] + requirements)
                    logger.info(f"Requirements installed/updated for {module_path.name}")
            except Exception as e:
                logger.error(f"Error installing requirements for {module_path.name}: {e}")

    def load_module(self, module_name):
        if module_name in self.loaded_modules:
            return False, f"Модуль `{module_name}` вже завантажено."

        module_path = self.MODULES_FOLDER / module_name
        if not module_path.is_dir():
            return False, f"Папку для модуля `{module_name}` не знайдено."
            
        self.install_module_requirements(module_path)
        
        for py_file in module_path.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            
            full_module_name = f"{module_path.name}.{py_file.stem}"
            try:
                spec = importlib.util.spec_from_file_location(full_module_name, py_file)
                if not spec: continue
                module = importlib.util.module_from_spec(spec)
                sys.modules[full_module_name] = module
                spec.loader.exec_module(module)
                
                module_handlers = []
                if hasattr(module, 'register_handlers'):
                    module_handlers = module.register_handlers(self.app)
                elif hasattr(module, 'add_on'):
                    module_handlers = module.add_on(self.app)

                # Store handlers as (handler, group) tuples
                if module_handlers and isinstance(module_handlers, list):
                    handler_tuples = []
                    for handler in module_handlers:
                        # Try to get group from handler, fallback to 0
                        group = getattr(handler, "group", 0)
                        handler_tuples.append((handler, group))
                    self.loaded_modules[module_name] = module
                    self.module_handlers[module_name] = handler_tuples
                    logger.info(f"Loaded module: {full_module_name}")
                    return True, f"Модуль `{module_name}` успішно завантажено."
                
            except Exception as e:
                logger.error(f"Error loading module {full_module_name}: {e}\n{traceback.format_exc()}")
                if full_module_name in sys.modules:
                    del sys.modules[full_module_name]
                return False, f"Помилка завантаження модуля `{module_name}`: {e}"
        
        return False, f"У модулі `{module_name}` не знайдено основної функції `register_handlers`."

    def unload_module(self, module_name):
        if module_name not in self.loaded_modules:
            return False, f"Модуль `{module_name}` не завантажено."

        if module_name in self.module_handlers:
            handlers_to_remove = self.module_handlers[module_name]
            for handler, group in handlers_to_remove:
                self.app.remove_handler(handler, group)
            del self.module_handlers[module_name]
        
        module = self.loaded_modules[module_name]
        full_module_names = [key for key in sys.modules if key.startswith(f"{module_name}.")]
        for key in full_module_names:
            del sys.modules[key]
        
        del self.loaded_modules[module_name]
        logger.info(f"Unloaded module: {module_name}")
        return True, f"Модуль `{module_name}` успішно вивантажено."

    def load_all_modules(self):
        for module_path in self.MODULES_FOLDER.iterdir():
            if module_path.is_dir():
                self.load_module(module_path.name)

    def check_for_updates(self):
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, 'app.py')
        try:
            response = requests.get(self.GITHUB_RAW_URL, timeout=10)
            if response.status_code == 200:
                with open(temp_file_path, 'w', encoding='utf-8') as temp_file:
                    temp_file.write(response.text)
                
                with open(__file__, 'r', encoding='utf-8') as local_file:
                    local_content = local_file.read()
                with open(temp_file_path, 'r', encoding='utf-8') as github_file:
                    github_content = github_file.read()
                
                if local_content != github_content:
                    logger.info("Update available for the main script.")
                    return True
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
        finally:
            shutil.rmtree(temp_dir)
        return False

    def apply_main_update(self):
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, 'app.py')
        try:
            response = requests.get(self.GITHUB_RAW_URL, timeout=10)
            if response.status_code == 200:
                with open(temp_file_path, 'w', encoding='utf-8') as temp_file:
                    temp_file.write(response.text)
                try:
                    self.app.send_message("me", "🆕 Updating main script and restarting...")
                except Exception:
                    pass
                shutil.copy2(temp_file_path, __file__)
                logger.info("Main script updated. Restarting...")
                os.execl(sys.executable, sys.executable, *sys.argv)
        except Exception as e:
            logger.error(f"Error applying main update: {e}")
        finally:
            shutil.rmtree(temp_dir)

    def auto_check_updates(self):
        while True:
            if self.check_for_updates():
                self.apply_main_update()
            time.sleep(self.CHECK_INTERVAL)

    def download_module(self, module_name):
        try:
            response = requests.get(f"{self.MODULES_REPO_URL}/{module_name}", timeout=10)
            if response.status_code == 200:
                files = response.json()
                module_path = self.MODULES_FOLDER / module_name
                module_path.mkdir(exist_ok=True)
                
                downloaded_files = 0
                for file_info in files:
                    if file_info['type'] == 'file':
                        file_response = requests.get(file_info['download_url'], timeout=10)
                        if file_response.status_code == 200:
                            file_path = module_path / file_info['name']
                            with open(file_path, 'wb') as f:
                                f.write(file_response.content)
                            downloaded_files += 1
                            logger.info(f"Downloaded {file_info['name']} for module {module_name}")
                
                if downloaded_files > 0:
                    logger.info(f"Successfully downloaded module {module_name} with {downloaded_files} files")
                    return True, f"Модуль `{module_name}` успішно завантажено."
                else:
                    return False, f"У репозиторії для модуля `{module_name}` не знайдено файлів."
            else:
                return False, f"Не вдалося знайти модуль `{module_name}` у репозиторії (помилка {response.status_code})."
        except Exception as e:
            logger.error(f"Error downloading module {module_name}: {e}")
            return False, f"Помилка завантаження модуля `{module_name}`: {e}"

    def create_local_module(self, module_name):
        module_path = self.MODULES_FOLDER / module_name
        if module_path.exists():
            return False, f"Модуль `{module_name}` вже існує."
        
        try:
            module_path.mkdir()
            main_file_path = module_path / f"{module_name}.py"
            boilerplate = """from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler

async def command_handler(client, message):
    await message.reply_text("Hello from your new module!")

def register_handlers(app: Client):
    return [
        MessageHandler(command_handler, filters.command("newcmd", prefixes=".") & filters.me),
    ]
"""
            with open(main_file_path, "w", encoding="utf-8") as f:
                f.write(boilerplate)
            
            return True, f"✅ Створено порожній модуль `{module_name}` з шаблоном у файлі `{main_file_path.name}`. Використовуйте `.load {module_name}`, щоб активувати."
        except Exception as e:
            logger.error(f"Error creating local module {module_name}: {e}")
            return False, f"❌ Помилка при створенні локального модуля: {e}"

    def delete_local_module(self, module_name):
        if module_name in self.loaded_modules:
            self.unload_module(module_name)
        
        module_path = self.MODULES_FOLDER / module_name
        if not module_path.is_dir():
            return False, f"❌ Локальний модуль `{module_name}` не знайдено."
        
        try:
            shutil.rmtree(module_path)
            return True, f"✅ Модуль `{module_name}` та всі його файли були повністю видалені."
        except Exception as e:
            logger.error(f"Error deleting local module {module_name}: {e}")
            return False, f"❌ Помилка видалення модуля: {e}"

    def setup_handlers(self):
        @self.app.on_message(filters.command("help", prefixes=".") & filters.user(self.sudo_users))
        async def help_command(client, message):
            if len(message.command) > 1 and message.command[1] == "modules":
                help_text = """
**🛠️ Керування модулями ModuBot**

**CREATE:**
`.createmodule <назва>` - Створити новий порожній модуль локально.
`.getmodule <назва>` - Завантажити модуль з репозиторію.

**READ:**
`.lsmodules` - Показати всі локальні модулі (завантажені/ні).
`.repomodules` - Показати всі модулі в онлайн-репозиторії.
`.modules` - Показати тільки завантажені модулі.
`.load <назва>` - Завантажити модуль в пам'ять.

**UPDATE:**
`.updatemodule <назва>` - Оновити модуль до останньої версії.
`.reload <назва>` - Перезавантажити модуль.

**DELETE:**
`.unload <назва>` - Вивантажити модуль з пам'яті.
`.delmodule <назва>` - Повністю видалити модуль.
"""
                await message.reply_text(help_text)
            else:
                await message.reply_text("Доступна довідка: `.help modules`")

        @self.app.on_message(filters.command("modules", prefixes=".") & filters.user(self.sudo_users))
        async def list_modules(client, message):
            if self.loaded_modules:
                modules_list = "\n".join([f"• `{mod}`" for mod in self.loaded_modules.keys()])
                text = f"**📦 Loaded Modules ({len(self.loaded_modules)}):**\n\n{modules_list}"
            else:
                text = "❌ No modules loaded."
            await message.reply_text(text)
        
        @self.app.on_message(filters.command("lsmodules", prefixes=".") & filters.user(self.sudo_users))
        async def list_local_modules(client, message):
            local_modules = [d.name for d in self.MODULES_FOLDER.iterdir() if d.is_dir()]
            if not local_modules:
                await message.reply_text("❌ Не знайдено жодного локального модуля.")
                return

            text = "**🗂️ Локальні модулі:**\n\n"
            for mod_name in sorted(local_modules):
                status = "✅ (завантажено)" if mod_name in self.loaded_modules else "➖ (не завантажено)"
                text += f"• `{mod_name}` {status}\n"
            
            await message.reply_text(text)

        @self.app.on_message(filters.command("repomodules", prefixes=".") & filters.user(self.sudo_users))
        async def list_repo_modules(client, message):
            status_msg = await message.reply_text("🌐 Отримую список модулів з репозиторію...")
            try:
                response = requests.get(self.MODULES_REPO_URL, timeout=10)
                response.raise_for_status()
                items = response.json()
                repo_modules = [item['name'] for item in items if item['type'] == 'dir']

                if not repo_modules:
                    await status_msg.edit_text("❌ В онлайн-репозиторії не знайдено модулів.")
                    return
                
                text = "**☁️ Доступні модулі в репозиторії:**\n\n"
                text += "\n".join([f"• `{mod_name}`" for mod_name in sorted(repo_modules)])
                await status_msg.edit_text(text)

            except requests.RequestException as e:
                await status_msg.edit_text(f"❌ Помилка доступу до GitHub: {e}")

        @self.app.on_message(filters.command("restart", prefixes=".") & filters.user(self.sudo_users))
        async def restart_bot(client, message):
            restart_message = await message.reply_text("🔄 Restarting bot...")
            restart_time = time.time()
            with open(self.RESTART_TIME_FILE, 'w') as f:
                f.write(f"{restart_time}\n{restart_message.chat.id}\n{restart_message.id}")
            logger.info("Restarting the bot...")
            os.execl(sys.executable, sys.executable, *sys.argv)

        @self.app.on_message(filters.command("addsudo", prefixes=".") & filters.me)
        async def add_sudo(client, message):
            if not message.reply_to_message:
                await message.reply_text("❌ Please reply to the user you want to give SUDO access to.")
                return
            
            user_id = message.reply_to_message.from_user.id
            if user_id in self.sudo_users:
                await message.reply_text("⚠️ User already has SUDO access.")
            else:
                self.save_sudo_user(user_id)
                username = message.reply_to_message.from_user.username or "Unknown"
                await message.reply_text(f"✅ User @{username} ({user_id}) has been given SUDO access.")

        @self.app.on_message(filters.command("checkupdate", prefixes=".") & filters.user(self.sudo_users))
        async def check_update_command(client, message):
            status_msg = await message.reply_text("🔍 Checking for updates...")
            if self.check_for_updates():
                await status_msg.edit_text("🆕 An update is available for the main script. Use `.restart` to apply.")
            else:
                await status_msg.edit_text("✅ No updates found. You're running the latest version.")

        @self.app.on_message(filters.command("createmodule", prefixes=".") & filters.user(self.sudo_users))
        async def create_module_cmd(client, message):
            if len(message.command) != 2:
                await message.reply_text("❌ Використання: `.createmodule <назва_модуля>`")
                return
            module_name = message.command[1]
            success, msg = self.create_local_module(module_name)
            await message.reply_text(msg)
            
        @self.app.on_message(filters.command("delmodule", prefixes=".") & filters.user(self.sudo_users))
        async def delete_module_cmd(client, message):
            if len(message.command) != 2:
                await message.reply_text("❌ Використання: `.delmodule <назва_модуля>`")
                return
            module_name = message.command[1]
            success, msg = self.delete_local_module(module_name)
            await message.reply_text(msg)

        @self.app.on_message(filters.command("getmodule", prefixes=".") & filters.user(self.sudo_users))
        async def get_module(client, message):
            if len(message.command) != 2:
                await message.reply_text("❌ Usage: `.getmodule module_name`")
                return
            
            module_name = message.command[1]
            status_msg = await message.reply_text(f"📥 Downloading module `{module_name}`...")
            
            success, msg = self.download_module(module_name)
            if success:
                await status_msg.edit_text(f"✅ Module `{module_name}` downloaded. Use `.load {module_name}` to activate.")
            else:
                await status_msg.edit_text(f"❌ Failed to download module `{module_name}`: {msg}")

        @self.app.on_message(filters.command("updatemodule", prefixes=".") & filters.user(self.sudo_users))
        async def update_module_cmd(client, message):
            if len(message.command) != 2:
                await message.reply_text("❌ Використання: `.updatemodule <назва_модуля>`")
                return
            
            module_name = message.command[1]
            module_path = self.MODULES_FOLDER / module_name
            if not module_path.is_dir():
                await message.reply_text(f"❌ Модуль `{module_name}` не знайдено локально. Використовуйте `.getmodule`, щоб завантажити його.")
                return

            status_msg = await message.reply_text(f"🔄 Оновлення модуля `{module_name}`...")
            
            was_loaded = module_name in self.loaded_modules
            if was_loaded:
                self.unload_module(module_name)
                await status_msg.edit_text(f"🔄 Модуль `{module_name}` вивантажено, починаю завантаження нової версії...")

            success, msg = self.download_module(module_name)
            if not success:
                await status_msg.edit_text(f"❌ Помилка оновлення: {msg}")
                if was_loaded:
                    self.load_module(module_name)
                return
            
            text = f"✅ Модуль `{module_name}` оновлено. "
            if was_loaded:
                load_success, load_msg = self.load_module(module_name)
                if load_success:
                    text += "і успішно перезавантажено."
                else:
                    text += f"але не вдалося перезавантажити: {load_msg}"
            
            await status_msg.edit_text(text)

        @self.app.on_message(filters.command("load", prefixes=".") & filters.user(self.sudo_users))
        async def load_cmd(client, message):
            if len(message.command) != 2:
                await message.reply_text("❌ Usage: `.load module_name`")
                return
            module_name = message.command[1]
            success, msg = self.load_module(module_name)
            await message.reply_text(f"{'✅' if success else '❌'} {msg}")

        @self.app.on_message(filters.command("unload", prefixes=".") & filters.user(self.sudo_users))
        async def unload_cmd(client, message):
            if len(message.command) != 2:
                await message.reply_text("❌ Usage: `.unload module_name`")
                return
            module_name = message.command[1]
            success, msg = self.unload_module(module_name)
            await message.reply_text(f"{'✅' if success else '❌'} {msg}")

        @self.app.on_message(filters.command("reload", prefixes=".") & filters.user(self.sudo_users))
        async def reload_cmd(client, message):
            if len(message.command) != 2:
                await message.reply_text("❌ Usage: `.reload module_name`")
                return
            module_name = message.command[1]
            status_msg = await message.reply_text(f"🔄 Reloading module `{module_name}`...")
            
            unload_success, _ = self.unload_module(module_name)
            if not unload_success and module_name in self.loaded_modules:
                 await status_msg.edit_text(f"❌ Failed to unload module `{module_name}`.")
                 return

            load_success, load_msg = self.load_module(module_name)
            if load_success:
                await status_msg.edit_text(f"✅ Module `{module_name}` successfully reloaded.")
            else:
                await status_msg.edit_text(f"❌ Failed to reload module `{module_name}`: {load_msg}")

        @self.app.on_message(filters.command("status", prefixes=".") & filters.user(self.sudo_users))
        async def bot_status(client, message):
            uptime = datetime.now() - datetime.strptime(self.last_restart_time, "%Y/%d/%m(%B) %H:%M:%S")
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            
            status_text = f"""
**🤖 ModuBot Status**

**👤 Owner:** {self.owner_nickname}
**🕐 Last Restart:** {self.last_restart_time}
**⏱ Uptime:** {str(uptime).split('.')[0]}
**📦 Modules:** {len(self.loaded_modules)}
**👥 SUDO Users:** {len(self.sudo_users)}

**💻 System Info:**
**CPU:** {cpu_percent}%
**RAM:** {memory.percent}% ({memory.used // 1024 // 1024} MB / {memory.total // 1024 // 1024} MB)
**Platform:** {platform.system()} {platform.release()}
"""
            await message.reply_text(status_text)

        if os.path.exists(self.RESTART_TIME_FILE):
            try:
                with open(self.RESTART_TIME_FILE, 'r') as f:
                    lines = f.readlines()
                    if len(lines) >= 3:
                        restart_time = float(lines[0].strip())
                        chat_id = int(lines[1].strip())
                        message_id = int(lines[2].strip())
                        
                        restart_duration = time.time() - restart_time
                        try:
                            self.app.edit_message_text(
                                chat_id, message_id, 
                                f"✅ Bot restarted successfully in {restart_duration:.2f}s"
                            )
                        except Exception:
                            pass
                os.remove(self.RESTART_TIME_FILE)
            except Exception as e:
                logger.error(f"Error handling restart notification: {e}")

    def initialize(self):
        self.display_logo()
        
        if not os.path.exists('.env'):
            self.out_of_box_experience()
        
        load_dotenv()
        
        api_id = os.getenv('API_ID')
        api_hash = os.getenv('API_HASH')
        
        if not api_id or not api_hash:
            logger.error("API credentials not found. Please set API_ID and API_HASH in .env file.")
            sys.exit(1)
        
        self.owner_nickname = os.getenv('OWNER_NICKNAME', 'Nobody')
        self.bot_firstname = os.getenv('BOT_FIRSTNAME', 'ModuBot')
        
        self.app = Client("my_userbot", api_id=api_id, api_hash=api_hash)
        self.load_sudo_users()

        with self.app:
            me = self.app.get_me()
            owner_id = me.id if me else None
        
        if owner_id and owner_id not in self.sudo_users:
            self.save_sudo_user(owner_id)
            logger.info(f"Owner with ID {owner_id} automatically added to SUDO users.")

        logger.info(f"Initializing ModuBot for {self.owner_nickname}")
        
        self.setup_handlers()
        self.load_all_modules()
        
        update_thread = threading.Thread(target=self.auto_check_updates, daemon=True)
        update_thread.start()
        
        logger.info(f"ModuBot started with {len(self.loaded_modules)} modules loaded")

    def run(self):
        self.initialize()
        self.app.run()

if __name__ == "__main__":
    LOCK_FILE = "modubot.lock"
    
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.read())
            if psutil.pid_exists(pid):
                logger.error(f"Another instance of ModuBot is already running with PID {pid}. Exiting.")
                sys.exit(1)
            else:
                logger.warning("Found a stale lock file. Removing it.")
        except (IOError, ValueError):
             logger.warning("Found a corrupted lock file. Removing it.")

    try:
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
            
        bot = ModuBot()
        bot.run()
        
    finally:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
        logger.info("ModuBot stopped. Lock file removed.")