import pytest
from unittest.mock import patch, MagicMock
import config
import notifier


def test_log_event_creates_file(tmp_path, monkeypatch):
    log_path = str(tmp_path / "events.log")
    monkeypatch.setattr(config, "LOG_PATH", log_path)
    notifier.log_event(42, "k@test.de", "web")
    assert (tmp_path / "events.log").exists()


def test_log_event_contains_lead_info(tmp_path, monkeypatch):
    log_path = str(tmp_path / "events.log")
    monkeypatch.setattr(config, "LOG_PATH", log_path)
    notifier.log_event(42, "k@test.de", "Probefahrt")
    content = open(log_path).read()
    assert "NEW LEAD id=42" in content
    assert "k@test.de" in content
    assert "Probefahrt" in content


def test_log_event_appends(tmp_path, monkeypatch):
    log_path = str(tmp_path / "events.log")
    monkeypatch.setattr(config, "LOG_PATH", log_path)
    notifier.log_event(1, "a@test.de", None)
    notifier.log_event(2, "b@test.de", None)
    lines = open(log_path).readlines()
    assert len(lines) == 2


def test_send_email_skips_when_smtp_not_configured(monkeypatch):
    monkeypatch.setattr(config, "SMTP_USER", "")
    notifier.send_email(1, "Klaus", "k@test.de", "web", None)


def test_send_email_calls_smtp_when_configured(monkeypatch):
    monkeypatch.setattr(config, "SMTP_USER", "from@test.de")
    monkeypatch.setattr(config, "SMTP_PASS", "pass123")
    monkeypatch.setattr(config, "MANAGER_EMAIL", "mgr@test.de")
    monkeypatch.setattr(config, "SMTP_HOST", "smtp.test.de")
    monkeypatch.setattr(config, "SMTP_PORT", 587)

    mock_smtp_instance = MagicMock()
    with patch("notifier.smtplib.SMTP") as mock_smtp_class:
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_smtp_instance)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)
        notifier.send_email(1, "Klaus", "k@test.de", "web", "VW Tiguan")
        mock_smtp_class.assert_called_once_with("smtp.test.de", 587)
        mock_smtp_instance.starttls.assert_called_once()
        mock_smtp_instance.login.assert_called_once_with("from@test.de", "pass123")


def test_send_email_logs_error_on_smtp_failure(monkeypatch, caplog):
    monkeypatch.setattr(config, "SMTP_USER", "from@test.de")
    monkeypatch.setattr(config, "SMTP_PASS", "pass")
    monkeypatch.setattr(config, "MANAGER_EMAIL", "mgr@test.de")
    monkeypatch.setattr(config, "SMTP_HOST", "smtp.test.de")
    monkeypatch.setattr(config, "SMTP_PORT", 587)

    with patch("notifier.smtplib.SMTP", side_effect=ConnectionRefusedError("refused")):
        import logging
        with caplog.at_level(logging.ERROR, logger="notifier"):
            notifier.send_email(1, "Klaus", "k@test.de", None, None)
    assert "Failed to send email" in caplog.text
