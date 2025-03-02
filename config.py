import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID"))
YEARLY_GROUP_ID = int(os.getenv("YEARLY_GROUP_ID"))
LIFETIME_GROUP_ID = int(os.getenv("LIFETIME_GROUP_ID"))
