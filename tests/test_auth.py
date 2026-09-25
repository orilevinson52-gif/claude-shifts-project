import pytest

import auth


def test_correct_password_verifies():
    stored = auth.hash_password("correct horse")
    assert auth.verify_password("correct horse", stored)


def test_wrong_password_is_rejected():
    stored = auth.hash_password("correct horse")
    assert not auth.verify_password("wrong horse", stored)


def test_same_password_gets_a_different_salt_each_time():
    assert auth.hash_password("same password") != auth.hash_password("same password")


def test_password_is_not_stored_in_plain_text():
    assert "secret-pass" not in auth.hash_password("secret-pass")


@pytest.mark.parametrize("stored", ["", "garbage", None, "md5$1$aa$bb"])
def test_malformed_hash_is_rejected(stored):
    assert not auth.verify_password("anything", stored)


@pytest.mark.parametrize(
    "username, password",
    [
        ("ab", "longenough"),
        ("x" * 51, "longenough"),
        ("   ", "longenough"),
        ("valid_user", "short"),
    ],
)
def test_register_validates_before_touching_the_database(monkeypatch, username, password):
    def fail_if_called():
        raise AssertionError("database should not be reached for invalid input")

    monkeypatch.setattr(auth, "get_connection", fail_if_called)

    with pytest.raises(auth.RegistrationError):
        auth.register(username, password)


def test_authenticate_with_empty_credentials_skips_the_database(monkeypatch):
    def fail_if_called():
        raise AssertionError("database should not be reached for empty input")

    monkeypatch.setattr(auth, "get_connection", fail_if_called)

    assert auth.authenticate("", "whatever") is None
    assert auth.authenticate("user", "") is None


@pytest.mark.parametrize(
    "username, admin_username, expected",
    [
        ("ori", "ori", True),
        ("Ori", "ori", True),  # usernames are unique case-insensitively
        (" ori ", "ori", True),
        ("someone", "ori", False),
        ("ori", "", False),  # no admin configured -> nobody is admin
        ("", "", False),
        (None, "ori", False),
    ],
)
def test_is_admin(username, admin_username, expected):
    assert auth.is_admin(username, admin_username) is expected


def test_reset_password_rejects_short_password_before_touching_the_database(monkeypatch):
    def fail_if_called():
        raise AssertionError("database should not be reached for invalid input")

    monkeypatch.setattr(auth, "get_connection", fail_if_called)

    with pytest.raises(auth.RegistrationError):
        auth.reset_password(1, "short")
