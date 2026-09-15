"""Tests for PII masking and session store.

PII masker tests use no external dependencies — just regex logic.
Session store tests mock Redis so no container is needed.
"""

from unittest.mock import MagicMock, call, patch

import pytest

from app.pii_masker import mask, unmask


# ── PII masker ────────────────────────────────────────────────────────────────


def test_masks_account_number():
    result = mask("My account is 9001234567890")
    assert "9001234567890" not in result.masked_text
    assert "[ACCOUNT]" in result.masked_text


def test_masks_phone_number():
    result = mask("Call me on 9812345678")
    assert "9812345678" not in result.masked_text
    assert "[PHONE]" in result.masked_text


def test_masks_email():
    result = mask("Email me at ananya@example.com")
    assert "ananya@example.com" not in result.masked_text
    assert "[EMAIL]" in result.masked_text


def test_masks_pan():
    result = mask("My PAN is ABCDE1234F")
    assert "ABCDE1234F" not in result.masked_text
    assert "[PAN]" in result.masked_text


def test_masks_aadhaar():
    result = mask("Aadhaar: 2345 6789 0123")
    assert "2345 6789 0123" not in result.masked_text
    assert "[AADHAAR]" in result.masked_text


def test_unmask_restores_original():
    result = mask("My account is 9001234567890 and phone is 9812345678")
    restored = unmask(result.masked_text, result.mapping)
    assert "9001234567890" in restored
    assert "9812345678" in restored


def test_same_value_gets_same_token():
    """The same account number appearing twice should use the same token."""
    result = mask("Account 9001234567890 and again 9001234567890")
    assert result.masked_text.count("[ACCOUNT]") == 2
    assert len(result.mapping) == 1  # only one entry in the mapping


def test_different_values_get_numbered_tokens():
    result = mask("Accounts: 9001234567890 and 9009876543210")
    assert "[ACCOUNT]" in result.masked_text
    assert "[ACCOUNT_2]" in result.masked_text


def test_text_with_no_pii_unchanged():
    result = mask("What is my account balance?")
    assert result.masked_text == "What is my account balance?"
    assert result.mapping == {}


def test_unmask_with_empty_mapping():
    assert unmask("Hello world", {}) == "Hello world"


# ── session store ─────────────────────────────────────────────────────────────


@patch("app.session_store.r")
def test_add_message_stores_json(mock_redis):
    from app.session_store import add_message
    add_message("sess123", "user", "hello")
    mock_redis.rpush.assert_called_once()
    mock_redis.expire.assert_called_once_with("session:sess123", 1800)


@patch("app.session_store.r")
def test_get_history_returns_messages(mock_redis):
    import json
    from app.session_store import get_history
    mock_redis.lrange.return_value = [
        json.dumps({"role": "user", "content": "hello"}),
        json.dumps({"role": "assistant", "content": "hi there"}),
    ]
    history = get_history("sess123")
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["content"] == "hi there"


@patch("app.session_store.r")
def test_clear_session_deletes_key(mock_redis):
    from app.session_store import clear_session
    clear_session("sess123")
    mock_redis.delete.assert_called_once_with("session:sess123")