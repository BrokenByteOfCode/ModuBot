import logging
import shutil
import time
from pathlib import Path
from . import config

logger = logging.getLogger(__name__)

def fill_console_with_background(color_code):
    background = f'\033[{color_code}m'
    clear_screen = '\033[2J'
    move_cursor_top_left = '\033[H'
    print(background + clear_screen + move_cursor_top_left, end='')

def display_logo():
    try:
        fill_console_with_background('44')
        if config.CONSOLE_LOGO_FILE.exists():
            with open(config.CONSOLE_LOGO_FILE, 'r', encoding='utf-8') as f:
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

def out_of_box_experience():
    fill_console_with_background('12')
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