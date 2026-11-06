"""Structured logging and redaction tests."""

from __future__ import annotations

import json
import logging

from cybersentinel.core.logging import (
    JsonFormatter,
    clear_correlation_id,
    set_correlation_id,
)


def test_json_formatter_includes_correlation_id() -> None:
    set_correlation_id("01JBQ8Z3K4M2N7P9R1S6T8V0WX")
    try:
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0, msg="hello", args=(), exc_info=None  # noqa: E501
        )
        output = JsonFormatter().format(record)
        payload = json.loads(output)
        assert payload["correlation_id"] == "01JBQ8Z3K4M2N7P9R1S6T8V0WX"
        assert payload["message"] == "hello"
    finally:
        clear_correlation_id()


def test_json_formatter_redacts_api_keys() -> None:
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="request failed api_key=AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ01234",
        args=(),
        exc_info=None,
    )
    output = JsonFormatter().format(record)
    assert "AIza" not in output
