"""
Personal AI OS - WebSocket API
实时更新接口
"""
import json
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """接受连接"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        """断开连接"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_to_user(self, user_id: str, message: dict):
        """发送消息给用户"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

    async def broadcast(self, message: dict):
        """广播消息给所有用户"""
        for user_id in self.active_connections:
            await self.send_to_user(user_id, message)


# 全局连接管理器
manager = ConnectionManager()


@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    WebSocket 连接端点

    用于实时推送洞察、预测和通知。
    """
    # 验证 token
    try:
        from app.core.security import decode_token
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001)
            return
    except Exception:
        await websocket.close(code=4001)
        return

    # 接受连接
    await manager.connect(websocket, user_id)

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message = json.loads(data)

            # 处理不同类型的消息
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif message.get("type") == "subscribe":
                # 订阅特定频道
                channel = message.get("channel", "general")
                await websocket.send_json({
                    "type": "subscribed",
                    "channel": channel
                })
            elif message.get("type") == "get_context":
                # 获取当前上下文
                from app.services.context_awareness import get_context_awareness_engine
                from app.core.database import async_session_factory

                async with async_session_factory() as db:
                    engine = get_context_awareness_engine(db)
                    context = await engine.get_current_context(user_id)
                    await websocket.send_json({
                        "type": "context_update",
                        "data": {
                            "mood": context.current_mood,
                            "energy": context.energy_level,
                            "focus": len(context.active_focus)
                        }
                    })

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception:
        manager.disconnect(websocket, user_id)


async def notify_user(user_id: str, notification_type: str, data: dict):
    """
    通知用户

    用于主动推送洞察、预测等。
    """
    await manager.send_to_user(user_id, {
        "type": "notification",
        "notification_type": notification_type,
        "data": data
    })
