import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is required")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "7807771944").split(",") if x]
DB_URL = "sqlite+aiosqlite:///bot/database.db"
