import hashlib
import hmac
import secrets

import mysql.connector

from config import ADMIN_USERNAME
from db.connection import create_user, get_connection, get_user_by_username, set_user_password
from scripts.init_db import seed_default_roles

PBKDF2_ITERATIONS = 600_000
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 50
MIN_PASSWORD_LENGTH = 8


class RegistrationError(Exception):
    """Raised with a user-facing (Hebrew) message when sign-up or a password change is rejected."""


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password, stored_hash):
    try:
        algorithm, iterations, salt_hex, digest_hex = stored_hash.split("$")
    except (AttributeError, ValueError):
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
    )
    return hmac.compare_digest(digest.hex(), digest_hex)


def validate_password(password):
    if len(password or "") < MIN_PASSWORD_LENGTH:
        raise RegistrationError(f"הסיסמה חייבת להכיל לפחות {MIN_PASSWORD_LENGTH} תווים")


def is_admin(username, admin_username=None):
    """True only for the configured admin account; with no admin configured, nobody is."""
    admin_username = ADMIN_USERNAME if admin_username is None else admin_username
    if not admin_username or not username:
        return False
    # Usernames are unique case-insensitively in the DB, so compare the same way
    return username.strip().casefold() == admin_username.strip().casefold()


def reset_password(user_id, new_password):
    validate_password(new_password)
    conn = get_connection()
    try:
        set_user_password(conn, user_id, hash_password(new_password))
    finally:
        conn.close()


def register(username, password):
    """Creates an account with the default roles and returns its user ID."""
    username = (username or "").strip()
    password = password or ""

    if not MIN_USERNAME_LENGTH <= len(username) <= MAX_USERNAME_LENGTH:
        raise RegistrationError(
            f"שם המשתמש חייב להכיל בין {MIN_USERNAME_LENGTH} ל־{MAX_USERNAME_LENGTH} תווים"
        )
    validate_password(password)

    conn = get_connection()
    try:
        user_id = create_user(conn, username, hash_password(password))
        seed_default_roles(conn, user_id)
        conn.commit()
        return user_id
    except mysql.connector.IntegrityError:
        conn.rollback()
        raise RegistrationError("שם המשתמש הזה כבר תפוס")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def authenticate(username, password):
    """Returns the user ID for valid credentials, otherwise None."""
    username = (username or "").strip()
    if not username or not password:
        return None

    conn = get_connection()
    try:
        user = get_user_by_username(conn, username)
    finally:
        conn.close()

    if user and verify_password(password, user["Password_Hash"]):
        return user["ID"]
    return None
