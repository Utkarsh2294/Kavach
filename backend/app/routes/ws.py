"""
Phase 09B — `/ws/feed` real-time WebSocket feed.

Auth: the client opens `ws://host/ws/feed?token=<jwt_access_token>&sandbox=<0|1>`.
Browsers cannot set WS headers, so the access token travels as a query param
(Phase 11's frontend will pass the stored access token here). The token is
decoded JWT-side; org scoping comes from the token's `org_id`, and a client
authenticated to org A is subserved ONLY org A's feed (cross-org leak gate).

On connect:
  1. Send one `graph_snapshot` (current delegation tree for this org/sandbox).
  2. Subscribe to the per-org/sandbox Redis pub/sub channel and forward every
     `transaction_update` / `agent_status_update` / `trust_score_update` the
     pipeline publishes. The mock live-data generator produced these EXACT
     shapes; this real feed is byte-for-byte identical (see services/feed.py).

Graceful reconnect: a dropped client only cancels its own listener task —
the broadcast loop and other clients are unaffected.
"""

import asyncio
import json
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError

from app.database import async_session_factory
from app.models import Agent
from app.config import get_settings
from app.auth import decode_token
from app.redis_client import RedisClient
from app.services.feed import graph_snapshot_for_agents

router = APIRouter(tags=["Real-time Feed"])


async def _verify_token(token: str) -> dict | None:
    try:
        payload = decode_token(token)
    except (JWTError, Exception):
        return None
    if payload.get("type") != "access":
        return None
    return payload


async def _send_snapshot(ws: WebSocket, db: AsyncSession, org_id, sandbox: bool) -> None:
    stmt = select(Agent).where(Agent.org_id == org_id, Agent.is_sandbox == sandbox)
    res = await db.execute(stmt)
    agents = list(res.scalars().all())
    snapshot = await graph_snapshot_for_agents(agents, sandbox=sandbox)
    await ws.send_json(snapshot)


async def _listener(ws: WebSocket, pubsub, channel: str, stop: asyncio.Event) -> None:
    try:
        await pubsub.subscribe(channel)
        while not stop.is_set():
            msg = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
            if msg is None:
                continue
            data = msg.get("data")
            if isinstance(data, bytes):
                data = data.decode("utf-8", errors="replace")
            if isinstance(data, str):
                await ws.send_text(data)  # already JSON-encoded by publish
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        try:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()
        except Exception:
            pass


@router.websocket("/ws/feed")
async def ws_feed(
    ws: WebSocket,
    token: str = Query(..., description="JWT access token"),
    sandbox: str = Query("0"),
):
    payload = await _verify_token(token)
    if payload is None:
        await ws.close(code=4401)  # unauthorized
        return
    try:
        org_id = uuid.UUID(payload["org_id"])
    except (KeyError, ValueError):
        await ws.close(code=4401)
        return
    is_sandbox = sandbox in ("1", "true", "True", "yes")
    channel = RedisClient.feed_channel(str(org_id), is_sandbox)

    await ws.accept()

    # 1. Send the current graph snapshot immediately on connect.
    async with async_session_factory() as db:
        await _send_snapshot(ws, db, org_id, is_sandbox)

    # 2. Forward pub/sub events to this client until disconnect.
    pubsub, _ = RedisClient.feed_pubsub(str(org_id), is_sandbox)
    stop = asyncio.Event()
    listener_task = asyncio.create_task(_listener(ws, pubsub, channel, stop))
    try:
        while True:
            # The feed is read-only telemetry; we still drain client frames so the
            # socket stays alive and we observe client-side disconnects promptly.
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        stop.set()
        try:
            await asyncio.wait_for(listener_task, timeout=3.0)
        except (asyncio.TimeoutError, Exception):
            listener_task.cancel()
        try:
            await ws.close()
        except Exception:
            pass
