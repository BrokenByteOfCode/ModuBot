**Welcome to ModuBot, your friendly Telegram UserBot powered by PyroGram!**

**Setup & Running**

The setup process is now fully automated. All you need is Python 3.8+ installed on your system.

The start script will automatically:
1.  Check for a virtual environment.
2.  Create one if it doesn't exist.
3.  Install all the necessary libraries from `requirements.txt`.
4.  Run the bot.

**On Windows:**
Simply double-click `StartBotOnWindows.bat`.
The first time you run it, a command prompt window will appear, create the environment, install packages, and then launch the bot. Subsequent launches will be much faster.

**On Linux:**
1.  First, make the script executable (you only need to do this once):
    ```bash
    chmod +x StartBotOnLinux.sh
    ```
2.  Then, run the script:
    ```bash
    ./StartBotOnLinux.sh
    ```
The script will handle the rest.

**First-Time Configuration**
When you run the bot for the first time, it will ask for your `API_ID`, `API_HASH`, and `OWNER_NICKNAME` in the console. It will also ask for your phone number, password (if you have one), and a 2FA code to log into your Telegram account.

**Conclusion and Recommendations**

You're all set! ModuBot is up and running. Enjoy exploring its features and customizations.

Don't forget, you can create your own modules too! Check out the `TemplateOfModule` directory to get started with creating modules for ModuBot!