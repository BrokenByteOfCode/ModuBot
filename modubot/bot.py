import logging
import os
import sys
from datetime import datetime
from pyrogram import Client, idle
from . import config, console_ui, utils
from .module_system import ModuleSystem
from .updater import Updater
from .handlers import register_handlers

logger = logging.getLogger(__name__)

class ModuBot:
    def __init__(self):
        self.start_time = datetime.now()
        
        if not all([config.API_ID, config.API_HASH, os.getenv('PYROGRAM_SESSION')]):
            if not os.path.exists('.env'):
                console_ui.out_of_box_experience()
                from importlib import reload
                reload(config)

        if not config.API_ID or not config.API_HASH:
            logger.error("API_ID та API_HASH не знайдено. Встановіть їх у .env або змінних середовища.")
            sys.exit(1)
        
        session_string = os.getenv('PYROGRAM_SESSION')
        if not session_string:
            logger.error("PYROGRAM_SESSION не встановлено. Запустіть generate_session.py для її створення.")
            sys.exit(1)

        self.app = Client(
            name="my_userbot_session",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=session_string
        )
        
        self.sudo_users = utils.load_sudo_users()
        self.module_system = ModuleSystem(self.app)
        self.updater = Updater(self.app)

    def run(self):
        console_ui.display_logo()
        
        logger.info(f"Ініціалізація ModuBot для {config.OWNER_NICKNAME}")
        register_handlers(self)
        self.module_system.load_all_modules()
        logger.info(f"Завантажено {len(self.module_system.loaded_modules)} модулів.")

        logger.info("Запуск клієнта...")
        
        # Використовуємо один блок 'with' для всього життєвого циклу
        with self.app:
            try:
                # --- Цей код виконується ПІСЛЯ успішного підключення ---
                me = self.app.get_me()
                if me and me.id not in self.sudo_users:
                    self.sudo_users.append(me.id)
                    utils.save_sudo_users(self.sudo_users)
                    logger.info(f"Власник {me.id} успішно доданий до SUDO-користувачів.")
                
                # Обробляємо сповіщення про перезапуск
                utils.handle_restart_notification(self.app)
                
            except Exception as e:
                logger.error(f"Помилка під час виконання завдань після запуску: {e}")
                logger.error("Перевірте правильність API-ключів та рядка сесії.")
                sys.exit(1)
            
            logger.info("Бот успішно запущено та готовий до роботи.")
            
            # idle() - це команда, яка змушує скрипт "заснути" і чекати на оновлення
            # від Telegram, доки його не зупинять (наприклад, через Ctrl+C).
            idle()
        
        logger.info("Бот зупинено.")