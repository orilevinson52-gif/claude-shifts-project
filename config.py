import os

from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "shift_scheduler"),
}

if os.getenv("DB_SSL_CA"):
    DB_CONFIG["ssl_ca"] = os.getenv("DB_SSL_CA")
    DB_CONFIG["ssl_verify_cert"] = True

MIN_REST_HOURS = 8

APP_PORT = int(os.getenv("PORT", "8080"))
