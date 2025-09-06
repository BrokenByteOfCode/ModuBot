import logging
import sys
import subprocess
import shutil
import importlib.util
import traceback
import requests
from . import config

logger = logging.getLogger(__name__)

class ModuleSystem:
    def __init__(self, app):
        self.app = app
        self.loaded_modules = {}
        self.module_handlers = {}
        config.MODULES_FOLDER.mkdir(exist_ok=True)

    def install_module_requirements(self, module_path):
        reqs_file = module_path / "reqs.txt"
        if reqs_file.exists():
            try:
                with open(reqs_file, 'r', encoding='utf-8') as f:
                    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                
                if requirements:
                    logger.info(f"Installing/updating requirements for {module_path.name}")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "-U"] + requirements)
            except Exception as e:
                logger.error(f"Error installing requirements for {module_path.name}: {e}")

    def load_module(self, module_name):
        if module_name in self.loaded_modules:
            return False, f"Модуль `{module_name}` вже завантажено."

        module_path = config.MODULES_FOLDER / module_name
        if not module_path.is_dir():
            return False, f"Папку для модуля `{module_name}` не знайдено."
            
        self.install_module_requirements(module_path)
        
        for py_file in module_path.glob("*.py"):
            if py_file.name == "__init__.py": continue
            
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

                if module_handlers and isinstance(module_handlers, list):
                    handler_tuples = []
                    for handler in module_handlers:
                        group = getattr(handler, "group", 0)
                        self.app.add_handler(handler, group)
                        handler_tuples.append((handler, group))
                    
                    self.loaded_modules[module_name] = module
                    self.module_handlers[module_name] = handler_tuples
                    logger.info(f"Loaded module: {full_module_name}")
                    return True, f"Модуль `{module_name}` успішно завантажено."
                
            except Exception as e:
                logger.error(f"Error loading module {full_module_name}: {e}\n{traceback.format_exc()}")
                if full_module_name in sys.modules: del sys.modules[full_module_name]
                return False, f"Помилка завантаження модуля `{module_name}`: {e}"
        
        return False, f"У модулі `{module_name}` не знайдено основної функції."

    def unload_module(self, module_name):
        if module_name not in self.loaded_modules:
            return False, f"Модуль `{module_name}` не завантажено."

        if module_name in self.module_handlers:
            for handler, group in self.module_handlers[module_name]:
                self.app.remove_handler(handler, group)
            del self.module_handlers[module_name]
        
        full_module_names = [key for key in sys.modules if key.startswith(f"{module_name}.")]
        for key in full_module_names: del sys.modules[key]
        
        del self.loaded_modules[module_name]
        logger.info(f"Unloaded module: {module_name}")
        return True, f"Модуль `{module_name}` успішно вивантажено."

    def load_all_modules(self):
        for module_path in config.MODULES_FOLDER.iterdir():
            if module_path.is_dir():
                self.load_module(module_path.name)

    def download_module(self, module_name):
        try:
            response = requests.get(f"{config.MODULES_REPO_URL}/{module_name}", timeout=10)
            if response.status_code == 200:
                files = response.json()
                module_path = config.MODULES_FOLDER / module_name
                module_path.mkdir(exist_ok=True)
                
                for file_info in files:
                    if file_info['type'] == 'file':
                        file_response = requests.get(file_info['download_url'], timeout=10)
                        if file_response.status_code == 200:
                            with open(module_path / file_info['name'], 'wb') as f:
                                f.write(file_response.content)
                return True, f"Модуль `{module_name}` успішно завантажено."
            else:
                return False, f"Не вдалося знайти модуль (помилка {response.status_code})."
        except Exception as e:
            return False, f"Помилка завантаження: {e}"

    def create_local_module(self, module_name):
        module_path = config.MODULES_FOLDER / module_name
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
            with open(main_file_path, "w", encoding="utf-8") as f: f.write(boilerplate)
            return True, f"✅ Створено порожній модуль `{module_name}`."
        except Exception as e:
            return False, f"❌ Помилка при створенні: {e}"

    def delete_local_module(self, module_name):
        if module_name in self.loaded_modules:
            self.unload_module(module_name)
        
        module_path = config.MODULES_FOLDER / module_name
        if not module_path.is_dir():
            return False, f"❌ Локальний модуль `{module_name}` не знайдено."
        
        try:
            shutil.rmtree(module_path)
            return True, f"✅ Модуль `{module_name}` видалено."
        except Exception as e:
            return False, f"❌ Помилка видалення: {e}"