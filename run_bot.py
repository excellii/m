
# run_bot.py -- wrapper to run your bot with robust logging and automatic reloads.
# Usage:
# 1) Install requirements: pip install pyTelegramBotAPI
# 2) Place run_bot.py in the same folder as bot.py
# 3) Run: python run_bot.py
#
# This wrapper will:
# - Import your bot module (`bot.py`)
# - Start `bot.polling()` (if `bot` object exists)
# - Catch and log any exceptions (ImportError, runtime errors, etc.) to bot_run.log
# - Sleep and restart automatically on crashes (so you can deploy and observe logs)
# - Useful for hosting/debugging: gives you the exact traceback to send back for fixes.

import importlib
import logging
import sys
import time
import traceback
from pathlib import Path

LOG_FILE = Path("bot_run.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()],
)

RELOAD_INTERVAL = 2.0  # seconds before restart on crash

def run_bot_loop():
    logging.info("Starting run_bot wrapper. Will try to import bot.py and start polling.")
    while True:
        try:
            if "bot" in sys.modules:
                logging.info("Reloading existing bot module...")
                bot_module = importlib.reload(sys.modules["bot"])
            else:
                logging.info("Importing bot module for the first time...")
                bot_module = importlib.import_module("bot")
            
            # bot module must expose 'bot' (TeleBot instance)
            bot_instance = getattr(bot_module, "bot", None)
            if bot_instance is None:
                logging.error("The module 'bot' does not define a 'bot' variable (telebot.TeleBot instance).")
                logging.error("Make sure bot.py creates `bot = telebot.TeleBot(BOT_TOKEN)` at module level.")
                return
            
            logging.info("Starting bot.polling(). If there are ImportErrors or runtime exceptions they will be logged.")
            # safest polling call; timeout helps avoid long blocking on some environments
            try:
                bot_instance.polling(none_stop=True, timeout=20)
            except TypeError:
                # some telebot versions use polling(none_stop=True) without timeout keyword
                bot_instance.polling(none_stop=True)
            
            # If polling returns (stopped for some reason), wait and reload
            logging.warning("bot.polling() exited without exception. Will reload and restart after a short pause.")
            time.sleep(RELOAD_INTERVAL)
        
        except Exception as e:
            # Log full traceback to file
            logging.exception("Unhandled exception while running the bot. See traceback above.")
            # Also write a separate detailed traceback file for easy access
            tb_path = Path("bot_last_traceback.txt")
            with tb_path.open("w", encoding="utf-8") as fh:
                fh.write("Unhandled exception:\n")
                traceback.print_exc(file=fh)
            logging.info(f"Traceback written to {tb_path.resolve()}")
            time.sleep(RELOAD_INTERVAL)

if __name__ == "__main__":
    run_bot_loop()
