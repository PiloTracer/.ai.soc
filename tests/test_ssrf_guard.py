"""Tests for SOC-008-D: cloud-metadata / link-local egress guard on the proxy's
raw-request builder.
"""

from __future__ import annotations

import pytest

from strix.tools.proxy.caido_api import _is_blocked_connect_target, build_raw_request


@pytest.mark.parametrize(
    "host",
    [
        "169.254.169.254",  # AWS/Azure/GCP/DigitalOcean IMDS
        "169.254.170.2",  # ECS task metadata — still 169.254.0.0/16
        "100.100.100.200",  # Alibaba Cloud metadata
        "metadata.google.internal",
        "METADATA.GOOGLE.INTERNAL",  # case-insensitive
        "metadata",
        "fe80::1",  # IPv6 link-local
        "fd00:ec2::254",  # AWS IMDSv2 IPv6
    ],
)
def test_is_blocked_connect_target_true_for_metadata_and_link_local(host: str) -> None:
    assert _is_blocked_connect_target(host) is True


@pytest.mark.parametrize(
    "host",
    [
        "127.0.0.1",
        "localhost",
        "10.0.0.5",
        "192.168.1.1",
        "172.16.0.1",
        "example.com",
        "host.docker.internal",
        "8.8.8.8",
        "::1",
        "2001:db8::1",
    ],
)
def test_is_blocked_connect_target_false_for_legitimate_hosts(host: str) -> None:
    assert _is_blocked_connect_target(host) is False


def test_build_raw_request_rejects_metadata_url() -> None:
    with pytest.raises(ValueError, match="cloud-metadata/link-local"):
        build_raw_request(
            method="GET",
            url="http://169.254.169.254/latest/meta-data/",
            headers={},
            body="",
        )


def test_build_raw_request_rejects_bracketed_ipv6_metadata_url() -> None:
    with pytest.raises(ValueError, match="cloud-metadata/link-local"):
        build_raw_request(
            method="GET",
            url="http://[fd00:ec2::254]/latest/api/token",
            headers={},
            body="",
        )


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:8080/",
        "http://10.0.0.5/admin",
        "https://example.com/",
        "http://host.docker.internal:3000/",
    ],
)
def test_build_raw_request_allows_legitimate_targets(url: str) -> None:
    conn_info, raw = build_raw_request(method="GET", url=url, headers={}, body="")
    assert conn_info.host
    assert b"GET" in raw
