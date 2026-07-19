"""Regression tests for concurrency-safety fixes in strix.tools.proxy.caido_api.

``caido_sdk_client``'s ``GraphQLClient`` wraps every query/mutation in its own
transient connect()/disconnect() cycle around one shared aiohttp transport
(``gql.Client.execute_async`` does ``async with self as session:``). Two
concurrent calls on the same cached ``Client`` race on that transport: one's
connect() can fire while the other's connection is still open
(``TransportAlreadyConnected``), or one's teardown can close the connector out
from under the other's in-flight request (``ClientConnectionError: Connector
is closed``) — this is the exact production traceback these tests guard
against. Fixed by serializing every SDK call behind ``_GRAPHQL_LOCK``, and by
double-checked locking around client creation in ``get_client()``.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from strix.tools.proxy import caido_api


@pytest.fixture(autouse=True)
def _reset_module_state() -> Any:
    """Give every test its own lock instances bound to its own event loop.

    ``pytest-asyncio`` runs each ``async def test_...`` in a fresh event
    loop, but ``_GRAPHQL_LOCK``/``_CLIENT_CREATE_LOCK`` are module-level
    singletons that persist for the whole test session. ``asyncio.Lock``
    binds to whichever loop first acquires it, so reusing the same lock
    object across tests with different loops raises "bound to a different
    event loop". In production this never happens — there's exactly one
    event loop for the process's scan lifetime — so this reset is purely
    test isolation, not a workaround for a real bug.
    """
    caido_api._CLIENT_CACHE.clear()
    caido_api._GRAPHQL_LOCK = asyncio.Lock()
    caido_api._CLIENT_CREATE_LOCK = asyncio.Lock()
    yield
    caido_api._CLIENT_CACHE.clear()


class _ConcurrencyProbe:
    """Records the highest number of callers ever inside the guarded section."""

    def __init__(self) -> None:
        self.current = 0
        self.max_seen = 0
        self._counter_lock = asyncio.Lock()

    async def enter(self) -> None:
        async with self._counter_lock:
            self.current += 1
            self.max_seen = max(self.max_seen, self.current)
        await asyncio.sleep(0.02)

    async def exit(self) -> None:
        async with self._counter_lock:
            self.current -= 1


class _FakeRequestListBuilder:
    def __init__(self, probe: _ConcurrencyProbe) -> None:
        self._probe = probe

    def first(self, _n: int) -> _FakeRequestListBuilder:
        return self

    def filter(self, _f: str) -> _FakeRequestListBuilder:
        return self

    def after(self, _a: str) -> _FakeRequestListBuilder:
        return self

    def scope(self, _s: str) -> _FakeRequestListBuilder:
        return self

    def descending(self, *_a: Any) -> _FakeRequestListBuilder:
        return self

    def ascending(self, *_a: Any) -> _FakeRequestListBuilder:
        return self

    async def execute(self) -> str:
        await self._probe.enter()
        try:
            return "requests-page"
        finally:
            await self._probe.exit()


class _FakeRequestNamespace:
    def __init__(self, probe: _ConcurrencyProbe) -> None:
        self._probe = probe

    def list(self) -> _FakeRequestListBuilder:
        return _FakeRequestListBuilder(self._probe)

    async def get(self, _request_id: str, _opts: Any) -> str:
        await self._probe.enter()
        try:
            return "request-detail"
        finally:
            await self._probe.exit()


class _FakeGraphQLNamespace:
    def __init__(self, probe: _ConcurrencyProbe) -> None:
        self._probe = probe

    async def query(
        self,
        _document: str,
        variables: dict[str, Any] | None = None,  # noqa: ARG002 - matches real call signature
    ) -> dict[str, Any]:
        await self._probe.enter()
        try:
            return {"sitemapRootEntries": {"edges": [], "count": {"value": 0}}}
        finally:
            await self._probe.exit()


class _FakeScopeNamespace:
    def __init__(self, probe: _ConcurrencyProbe) -> None:
        self._probe = probe

    async def list(self) -> str:
        await self._probe.enter()
        try:
            return "scopes"
        finally:
            await self._probe.exit()


class _FakeClient:
    def __init__(self, probe: _ConcurrencyProbe) -> None:
        self.request = _FakeRequestNamespace(probe)
        self.graphql = _FakeGraphQLNamespace(probe)
        self.scope = _FakeScopeNamespace(probe)


async def test_list_requests_and_list_sitemap_never_run_concurrently() -> None:
    """Exact production scenario: list_requests_with_client and
    list_sitemap_with_client, invoked concurrently against the same cached
    client, must never both be mid-SDK-call at the same time.
    """
    probe = _ConcurrencyProbe()
    client = _FakeClient(probe)

    await asyncio.gather(
        caido_api.list_requests_with_client(client),
        caido_api.list_sitemap_with_client(client),
        caido_api.list_requests_with_client(client),
        caido_api.list_sitemap_with_client(client),
    )

    assert probe.max_seen == 1


async def test_scope_list_serializes_against_request_list() -> None:
    probe = _ConcurrencyProbe()
    client = _FakeClient(probe)

    await asyncio.gather(
        caido_api.list_requests_with_client(client),
        caido_api.scope_list(client),
    )

    assert probe.max_seen == 1


async def test_get_request_serializes_against_view_sitemap_entry() -> None:
    probe = _ConcurrencyProbe()
    client = _FakeClient(probe)

    await asyncio.gather(
        caido_api.get_request_with_client(client, "req-1"),
        caido_api.view_sitemap_entry_with_client(client, "entry-1"),
    )

    assert probe.max_seen == 1


async def test_get_client_creates_exactly_one_client_under_concurrent_callers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression test for the same class of bug in client *creation*: before
    the fix, N concurrent first-time callers of get_client() could each pass
    the empty-cache check and create + connect their own Client, leaking all
    but the last one. Only one Client must ever be constructed.
    """
    created: list[Any] = []

    class _FakeSdkClient:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            created.append(self)

        async def connect(self) -> None:
            await asyncio.sleep(0.02)  # widen the race window

    monkeypatch.setattr(caido_api, "Client", _FakeSdkClient)
    monkeypatch.setattr(caido_api, "_login_as_guest", lambda: "fake-token")

    clients = await asyncio.gather(*(caido_api.get_client() for _ in range(10)))

    assert len(created) == 1
    assert all(c is clients[0] for c in clients)
