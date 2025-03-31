import pytest
from services import api_client

class DummyResponse:
    def __init__(self, status, json_data=None):
        self.status = status
        self._json_data = json_data or {}
    async def json(self):
        return self._json_data

@pytest.mark.asyncio
async def test_search_speaker_success(monkeypatch):
    # Simulate a successful 200 response from the server
    async def dummy_post(url, json, timeout):
        return DummyResponse(status=200, json_data={"name": "Test User"})
    # Monkeypatch aiohttp.ClientSession
    class DummySession:
        def __enter__(self): return self
        def __exit__(self, exc_type, exc, tb): pass
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): pass
        async def post(self, url, json, timeout):
            return DummyResponse(status=200, json_data={"name": "Test User"})
    monkeypatch.setattr(api_client, "aiohttp", type("X", (), {"ClientSession": lambda *args, **kw: DummySession()}))
    result = await api_client.search_speaker("test user")
    assert result == {"name": "Test User"}

@pytest.mark.asyncio
async def test_search_speaker_not_found(monkeypatch):
    # Simulate a 404 response
    class DummySession:
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): pass
        async def post(self, url, json, timeout):
            return DummyResponse(status=404)
    monkeypatch.setattr(api_client, "aiohttp", type("X", (), {"ClientSession": lambda *args, **kw: DummySession()}))
    result = await api_client.search_speaker("nonexistent")
    assert result is None

@pytest.mark.asyncio
async def test_auth_chaperone_fail(monkeypatch):
    # Simulate a 401 Unauthorized
    class DummySession:
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): pass
        async def post(self, url, json, timeout):
            return DummyResponse(status=401)
    monkeypatch.setattr(api_client, "aiohttp", type("X", (), {"ClientSession": lambda *args, **kw: DummySession()}))
    with pytest.raises(api_client.ApiError) as excinfo:
        await api_client.auth_chaperone("user", "wrongpass")
    assert "Неверный логин" in str(excinfo.value)
