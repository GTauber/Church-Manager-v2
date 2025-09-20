import pytest
import httpx
from unittest.mock import AsyncMock, patch
from app.clients.waha_client import WAHAClient


@pytest.mark.asyncio
async def test_send_message_success():
    client = WAHAClient("http://test.local", "test-api-key")

    mock_response = AsyncMock()
    mock_response.status_code = 200

    with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
        result = await client.send_message("123456789@c.us", "Test message")

        mock_post.assert_called_once_with(
            "http://test.local/api/sendText",
            json={
                "session": "default",
                "chatId": "123456789@c.us",
                "text": "Test message"
            },
            headers={
                "Content-Type": "application/json",
                "X-Api-Key": "test-api-key"
            },
            timeout=10.0
        )

    assert result is True


@pytest.mark.asyncio
async def test_send_message_without_api_key():
    client = WAHAClient("http://test.local")

    mock_response = AsyncMock()
    mock_response.status_code = 200

    with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
        result = await client.send_message("123456789@c.us", "Test message", "custom-session")

        mock_post.assert_called_once_with(
            "http://test.local/api/sendText",
            json={
                "session": "custom-session",
                "chatId": "123456789@c.us",
                "text": "Test message"
            },
            headers={
                "Content-Type": "application/json"
            },
            timeout=10.0
        )

    assert result is True


@pytest.mark.asyncio
async def test_send_message_failure():
    client = WAHAClient("http://test.local")

    mock_response = AsyncMock()
    mock_response.status_code = 500

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        result = await client.send_message("123456789@c.us", "Test message")

    assert result is False


@pytest.mark.asyncio
async def test_send_message_timeout():
    client = WAHAClient("http://test.local")

    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Timeout")):
        result = await client.send_message("123456789@c.us", "Test message")

    assert result is False


@pytest.mark.asyncio
async def test_send_message_request_error():
    client = WAHAClient("http://test.local")

    with patch("httpx.AsyncClient.post", side_effect=httpx.RequestError("Connection failed")):
        result = await client.send_message("123456789@c.us", "Test message")

    assert result is False


@pytest.mark.asyncio
async def test_base_url_trailing_slash():
    client = WAHAClient("http://test.local/", "api-key")

    mock_response = AsyncMock()
    mock_response.status_code = 200

    with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
        await client.send_message("123456789@c.us", "Test")

        called_url = mock_post.call_args[0][0]
        assert called_url == "http://test.local/api/sendText"
        assert not called_url.endswith("//api/sendText")