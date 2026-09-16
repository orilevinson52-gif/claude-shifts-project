import os
import tempfile
import urllib.parse

from dotenv import load_dotenv

load_dotenv()


def _parse_database_url(url_str: str) -> dict:
    """Parse mysql://user:pass@host:port/dbname URL into connection params."""
    parsed = urllib.parse.urlparse(url_str)
    config = {}
    if parsed.hostname:
        config["host"] = parsed.hostname
    if parsed.port:
        config["port"] = int(parsed.port)
    if parsed.username:
        config["user"] = urllib.parse.unquote(parsed.username)
    if parsed.password:
        config["password"] = urllib.parse.unquote(parsed.password)
    if parsed.path and parsed.path != "/":
        config["database"] = parsed.path.lstrip("/").split("?")[0]
    return config


# 1. Base DB configuration (supports DATABASE_URL / MYSQL_URL or individual variables)
db_url = os.getenv("DATABASE_URL") or os.getenv("MYSQL_URL")
url_config = _parse_database_url(db_url) if db_url else {}

DB_CONFIG = {
    "host": os.getenv("DB_HOST", url_config.get("host", "localhost")),
    "port": int(os.getenv("DB_PORT", str(url_config.get("port", 3306)))),
    "user": os.getenv("DB_USER", url_config.get("user", "root")),
    "password": os.getenv("DB_PASSWORD", url_config.get("password", "")),
    "database": os.getenv("DB_NAME", url_config.get("database", "shift_scheduler")),
    # Force the pure-Python implementation: the compiled C extension fails to
    # load auth plugins (e.g. "Authentication plugin 'mysql_native_password'
    # cannot be loaded") on some platforms, including Windows.
    "use_pure": True,
}

DB_NAME = DB_CONFIG["database"]

# 2. SSL handling for cloud MySQL providers (Render, TiDB Cloud, Aiven, AWS RDS)
ssl_ca = os.getenv("DB_SSL_CA")
if ssl_ca:
    if os.path.isfile(ssl_ca):
        DB_CONFIG["ssl_ca"] = ssl_ca
    elif "-----BEGIN CERTIFICATE-----" in ssl_ca:
        # User pasted certificate content directly into environment variable
        temp_ca = os.path.join(tempfile.gettempdir(), "cloud_db_ca.pem")
        with open(temp_ca, "w", encoding="utf-8") as f:
            f.write(ssl_ca)
        DB_CONFIG["ssl_ca"] = temp_ca
    DB_CONFIG["ssl_verify_cert"] = True

# Fallback to system certificates on Linux/Render when connecting to remote cloud host
if "ssl_ca" not in DB_CONFIG:
    linux_ca = "/etc/ssl/certs/ca-certificates.crt"
    is_remote = DB_CONFIG["host"] not in ("localhost", "127.0.0.1")
    use_system_ca = os.getenv("DB_USE_SYSTEM_CA", "").lower() in ("1", "true", "yes")
    if (use_system_ca or is_remote) and os.path.isfile(linux_ca):
        DB_CONFIG["ssl_ca"] = linux_ca

# Allow disabling cert verification if cloud provider uses self-signed cert
verify_cert_env = os.getenv("DB_SSL_VERIFY_CERT")
if verify_cert_env is not None:
    DB_CONFIG["ssl_verify_cert"] = verify_cert_env.lower() not in ("0", "false", "no")

if os.getenv("DB_SSL_DISABLED", "").lower() in ("1", "true", "yes"):
    DB_CONFIG["ssl_disabled"] = True

# 3. Application flags and constants
MIN_REST_HOURS = 8
APP_PORT = int(os.getenv("PORT", "8080"))
AUTO_INIT_DB = os.getenv("AUTO_INIT_DB", "true").lower() in ("1", "true", "yes")
SEED_INITIAL_DATA = os.getenv("SEED_INITIAL_DATA", "false").lower() in ("1", "true", "yes")
