import os
import logging
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise ValueError("No API_TOKEN set for Telegram Bot.")


logger = logging.getLogger("telegram_bot")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("logs.log", encoding="utf-8")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)