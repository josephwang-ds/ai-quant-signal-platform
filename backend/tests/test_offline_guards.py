"""Offline guard contract tests for default CI."""

from __future__ import annotations

import socket

import pytest


def test_offline_suite_blocks_outbound_network() -> None:
    sock = socket.socket()
    with pytest.raises(OSError, match="Network access blocked"):
        sock.connect(("example.com", 80))
