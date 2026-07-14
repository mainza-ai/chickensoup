"""
Tests for P2-1: WebSocket streaming endpoint /ws/agent.

Requires the live server running on localhost:8000 and the `websockets` library.
"""
import json
import asyncio
import pytest
import websockets

from src.config import settings

WS_URL = "ws://localhost:8000/ws/agent"
BASE_HTTP = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json", "X-Api-Key": "dev"}


def _is_live_server_available():
    try:
        import requests
        return requests.get(f"{BASE_HTTP}/status", timeout=3).ok
    except Exception:
        return False


@pytest.mark.skipif(
    not _is_live_server_available(),
    reason="Live server not available",
)
class TestWebSocketStreaming:
    """End-to-end WebSocket protocol tests."""

    async def _connect_and_send(self, query: str, timeout: float = 30.0):
        """Helper: connect, send query, collect all messages until completed."""
        messages = []
        async with websockets.connect(WS_URL) as ws:
            await ws.send(query)
            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
                    msg = json.loads(raw)
                    messages.append(msg)
                    if msg.get("status") == "completed":
                        break
                except asyncio.TimeoutError:
                    break
        return messages

    def test_websocket_streaming_completes(self):
        messages = asyncio.run(self._connect_and_send("What is Area 51?"))
        statuses = [m.get("status") for m in messages]
        assert "completed" in statuses, f"Expected 'completed' in statuses, got: {statuses}"

    def test_websocket_returns_conversation_id(self):
        messages = asyncio.run(self._connect_and_send("Tell me about Bob Lazar"))
        completed = [m for m in messages if m.get("status") == "completed"]
        assert len(completed) > 0, "No 'completed' message received"
        conv_id = completed[-1].get("conversation_id")
        assert conv_id is not None and len(conv_id) > 0, "conversation_id missing or empty in completed message"

    def test_websocket_streaming_has_chunks(self):
        messages = asyncio.run(self._connect_and_send("What is the Philadelphia Experiment?"))
        has_chunk = any("chunk" in m for m in messages)
        assert has_chunk, f"Expected streaming chunks, got message keys: {[list(m.keys()) for m in messages]}"

    def test_websocket_answer_is_non_empty(self):
        messages = asyncio.run(self._connect_and_send("What is entropic gravity?"))
        completed = [m for m in messages if m.get("status") == "completed"]
        assert len(completed) > 0
        answer = completed[-1].get("answer", "")
        assert len(answer) > 10, f"Answer too short: {answer[:50]}"

    def test_websocket_error_handling(self):
        messages = asyncio.run(self._connect_and_send(""))
        # Empty query should not crash the WebSocket; should return completed or processing
        statuses = [m.get("status") for m in messages]
        assert len(messages) > 0, "No messages received for empty query"

    def test_websocket_first_message_is_processing(self):
        messages = asyncio.run(self._connect_and_send("What is Area 51?"))
        if len(messages) > 0:
            first_status = messages[0].get("status")
            assert first_status in ("processing", "streaming", "completed"), f"Unexpected first status: {first_status}"

    def test_websocket_concurrent_connections(self):
        """Two concurrent WebSocket connections should both complete."""
        async def run_two():
            results = await asyncio.gather(
                self._connect_and_send("What is Area 51?"),
                self._connect_and_send("Who is Bob Lazar?"),
            )
            return results

        results = asyncio.run(run_two())
        assert len(results) == 2
        for messages in results:
            statuses = [m.get("status") for m in messages]
            assert "completed" in statuses, f"Connection did not complete: {statuses}"
