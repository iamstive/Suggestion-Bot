from ast import literal_eval
from dotenv import load_dotenv
from pathlib import Path
from os import getenv


# * Main Config

BASE_DIR = Path(__file__).resolve().parent

DOTENV_PATH = BASE_DIR / '.env'

if DOTENV_PATH.exists():
    load_dotenv(DOTENV_PATH)

TOKEN = getenv('TOKEN')

MAIN_CHAT_ID = literal_eval(getenv('MAIN_CHAT_ID'))

BOT_ID = literal_eval(getenv('BOT_ID'))

CHANNEL_ID = literal_eval(getenv('CHANNEL_ID'))
