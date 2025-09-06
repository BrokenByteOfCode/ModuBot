import os
import sys
import time
import psutil
import platform
import requests
from datetime import datetime
from pyrogram import filters
from . import config, utils

def get_help_text(category=None):
    help_categories = {
        "basic": {"title": "🔧 Основні команди", "commands": [("`.status`", "Показати статус бота"),("`.restart`", "Перезапустити бота"),("`.addsudo`", "Додати SUDO користувача"),("`.checkupdate`", "Перевірити оновлення"),("`.update`", "Застосувати оновлення")]},
        "modules": {"title": "📦 Керування модулями", "commands": [("`.modules`", "Показати завантажені модулі"),("`.lsmodules`", "Показати всі локальні модулі"),("`.repomodules`", "Показати модулі в репозиторії"),("`.load <name>`", "Завантажити модуль"),("`.unload <name>`", "Вивантажити модуль"),("`.reload <name>`", "Перезавантажити модуль")]},
        "manage": {"title": "🛠️ Управління модулями", "commands": [("`.getmodule <name>`", "Завантажити модуль з репозиторію"),("`.updatemodule <name>`", "Оновити модуль"),("`.createmodule <name>`", "Створити новий модуль"),("`.delmodule <name>`", "Видалити модуль")]}
    }
    
    if category and category in help_categories:
        cat = help_categories[category]
        text = f"**{cat['title']}**\n\n" + "\n".join([f"`{cmd}` - {desc}" for cmd, desc in cat['commands']])
        return text
    
    text = "**🤖 ModuBot Help**\n\n**Доступні категорії:**\n"
    text += "`.help basic`\n`.help modules`\n`.help manage`\n\n"
    text += "`.help all` - показати всі команди"
    
    if category == "all":
        text = "**🤖 ModuBot - Всі команди**\n\n"
        for _, cat_data in help_categories.items():
            text += f"**{cat_data['title']}**\n" + "\n".join([f"`{cmd}` - {desc}" for cmd, desc in cat_data['commands']]) + "\n\n"
    return text

def register_handlers(bot):
    sudo_filter = filters.user(bot.sudo_users)

    @bot.app.on_message(filters.command("help", ".") & sudo_filter)
    async def help_command(client, message):
        category = message.command[1] if len(message.command) > 1 else None
        await message.reply_text(get_help_text(category))

    @bot.app.on_message(filters.command("modules", ".") & sudo_filter)
    async def list_modules(client, message):
        if bot.module_system.loaded_modules:
            modules_list = "\n".join([f"• `{mod}`" for mod in bot.module_system.loaded_modules.keys()])
            text = f"**📦 Loaded Modules ({len(bot.module_system.loaded_modules)}):**\n\n{modules_list}"
        else: text = "❌ No modules loaded."
        await message.reply_text(text)
    
    @bot.app.on_message(filters.command("lsmodules", ".") & sudo_filter)
    async def list_local_modules(client, message):
        local_modules = [d.name for d in config.MODULES_FOLDER.iterdir() if d.is_dir()]
        if not local_modules: return await message.reply_text("❌ Не знайдено локальних модулів.")
        text = "**🗂️ Локальні модулі:**\n\n"
        for mod_name in sorted(local_modules):
            status = "✅" if mod_name in bot.module_system.loaded_modules else "➖"
            text += f"• `{mod_name}` {status}\n"
        await message.reply_text(text)

    @bot.app.on_message(filters.command("repomodules", ".") & sudo_filter)
    async def list_repo_modules(client, message):
        status_msg = await message.reply_text("🌐 Отримую список...")
        try:
            items = requests.get(config.MODULES_REPO_URL, timeout=10).json()
            repo_modules = [item['name'] for item in items if item['type'] == 'dir']
            text = "**☁️ Доступні модулі:**\n\n" + "\n".join([f"• `{mod}`" for mod in sorted(repo_modules)])
            await status_msg.edit_text(text)
        except Exception as e: await status_msg.edit_text(f"❌ Помилка: {e}")

    @bot.app.on_message(filters.command("restart", ".") & sudo_filter)
    async def restart_bot(client, message):
        msg = await message.reply_text("🔄 Restarting...")
        with open(config.RESTART_TIME_FILE, 'w') as f:
            f.write(f"{time.time()}\n{msg.chat.id}\n{msg.id}")
        os.execl(sys.executable, sys.executable, *sys.argv)

    @bot.app.on_message(filters.command("addsudo", ".") & filters.me)
    async def add_sudo(client, message):
        if not message.reply_to_message: return await message.reply_text("❌ Reply to a user.")
        user_id = message.reply_to_message.from_user.id
        if user_id in bot.sudo_users: return await message.reply_text("⚠️ User already has SUDO.")
        bot.sudo_users.append(user_id)
        if utils.save_sudo_users(bot.sudo_users):
            await message.reply_text(f"✅ User {user_id} has been given SUDO.")
        else: await message.reply_text("❌ Failed to save SUDO users.")

    @bot.app.on_message(filters.command("checkupdate", ".") & sudo_filter)
    async def check_update_command(client, message):
        msg = await message.reply_text("🔍 Checking...")
        if bot.updater.check_for_updates(): await msg.edit_text("🆕 Update available. Use `.update`.")
        else: await msg.edit_text("✅ You're on the latest version.")

    @bot.app.on_message(filters.command("update", ".") & sudo_filter)
    async def apply_update_command(client, message):
        msg = await message.reply_text("🔍 Checking...")
        if bot.updater.check_for_updates():
            await msg.edit_text("🆕 Applying update and restarting...")
            bot.updater.apply_main_update()
        else: await msg.edit_text("✅ No updates available.")

    @bot.app.on_message(filters.command(["createmodule", "delmodule", "getmodule", "updatemodule", "load", "unload", "reload"], ".") & sudo_filter)
    async def module_management(client, message):
        command = message.command[0]
        if len(message.command) != 2: return await message.reply_text(f"❌ Usage: `.{command} <module_name>`")
        module_name = message.command[1]

        if command == "createmodule": success, msg = bot.module_system.create_local_module(module_name)
        elif command == "delmodule": success, msg = bot.module_system.delete_local_module(module_name)
        elif command == "load": success, msg = bot.module_system.load_module(module_name)
        elif command == "unload": success, msg = bot.module_system.unload_module(module_name)
        elif command == "getmodule":
            status_msg = await message.reply_text(f"📥 Downloading `{module_name}`...")
            success, msg = bot.module_system.download_module(module_name)
            return await status_msg.edit_text(msg)
        elif command == "reload":
            status_msg = await message.reply_text(f"🔄 Reloading `{module_name}`...")
            bot.module_system.unload_module(module_name)
            success, msg = bot.module_system.load_module(module_name)
            return await status_msg.edit_text(msg)
        elif command == "updatemodule":
            status_msg = await message.reply_text(f"🔄 Updating `{module_name}`...")
            was_loaded = module_name in bot.module_system.loaded_modules
            if was_loaded: bot.module_system.unload_module(module_name)
            success, dl_msg = bot.module_system.download_module(module_name)
            if not success: return await status_msg.edit_text(dl_msg)
            if was_loaded:
                success, load_msg = bot.module_system.load_module(module_name)
                msg = f"✅ Updated and reloaded." if success else f"✅ Updated, but failed to reload: {load_msg}"
            else: msg = f"✅ Updated."
            return await status_msg.edit_text(msg)

        await message.reply_text(msg)

    @bot.app.on_message(filters.command("status", ".") & sudo_filter)
    async def bot_status(client, message):
        uptime = datetime.now() - bot.start_time
        mem = psutil.virtual_memory()
        status_text = f"""**🤖 ModuBot Status**
**👤 Owner:** {config.OWNER_NICKNAME}
**⏱ Uptime:** {str(uptime).split('.')[0]}
**📦 Modules:** {len(bot.module_system.loaded_modules)}
**👥 SUDO:** {len(bot.sudo_users)}

**💻 System:**
**CPU:** {psutil.cpu_percent()}% | **RAM:** {mem.percent}%
**Platform:** {platform.system()} {platform.release()}"""
        await message.reply_text(status_text)