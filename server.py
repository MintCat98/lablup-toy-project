import asyncio
import json
import uuid

import aiohttp
from aiohttp import web
import redis.asyncio as redis
from aiohttp_session import get_session, setup
from aiohttp_session.redis_storage import RedisStorage
import pathlib


class WebServer:
    def __init__(self):
        # Config for Redis
        self.REDIS_HOST = 'redis'
        self.REDIS_PORT = 6379
        self.redis_client = redis.Redis(
            host=self.REDIS_HOST, port=self.REDIS_PORT)
        self.clients = {}

        # Base directory
        self.BASE_DIR = pathlib.Path(__file__).parent

    async def init_redis(self):
        # Create a connection pool for Redis
        redis_pool = redis.ConnectionPool(
            host=self.REDIS_HOST, port=self.REDIS_PORT)
        return redis.StrictRedis(connection_pool=redis_pool)

    async def create_app(self):
        # Create an aiohttp web application
        app = web.Application()
        redis_instance = await self.init_redis()
        setup(app, RedisStorage(redis_instance))

        app.router.add_get('/ws', self.websocket_handler)
        app.router.add_post('/set-nickname', self.set_nickname)
        app.router.add_get('/', self.index)
        app.router.add_static(
            '/static/', path=self.BASE_DIR / 'static', name='static')

        loop = asyncio.get_event_loop()
        loop.create_task(self.redis_subscriber())

        return app

    async def set_nickname(self, request):
        # Set a nickname for the user
        data = await request.json()
        nickname = data.get('nickname')
        session = await get_session(request)
        session_id = session.get('session_id', str(uuid.uuid4()))
        session['session_id'] = session_id

        # Check if the nickname is already in use
        existing_sessions = await self.redis_client.keys(f"user:{nickname}:*")
        if existing_sessions and f"user:{nickname}:{session_id}" not in existing_sessions:
            return web.json_response({'error': f'{nickname}은 이미 사용중인 닉네임입니다.'}, status=400)

        # Set the nickname in the session and Redis
        session['user_id'] = nickname
        await self.redis_client.set(f"user:{nickname}:{session_id}", "connected")
        return web.json_response({'message': f'{nickname} 닉네임 설정 완료'})

    async def index(self, request):
        # Serve the index.html file
        session = await get_session(request)
        user_id = session.get('user_id', '닉네임 없음')
        print(f"현재 세션 사용자: {user_id}")
        return web.FileResponse(self.BASE_DIR / 'templates/index.html')

    async def websocket_handler(self, request):
        # Handle WebSocket connections
        session = await get_session(request)
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        user_id = session.get('user_id')
        session_id = session.get('session_id')

        # Check if the user has set a nickname
        if not user_id:
            await ws.send_json({"error": "닉네임이 없습니다. 새로고침 후 다시 시도하세요."})
            await ws.close()
            return ws

        # Add the WebSocket connection to the list of clients
        self.clients[user_id] = ws
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe('chat_channel')

        # Send a message to all clients that a new user has joined
        join_message = {"sender": "system", "text": f"{user_id} 님이 입장하셨습니다."}
        await self.redis_client.publish('chat_channel', json.dumps(join_message))

        try:
            # Listen for messages from the client
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    if data.get("message") == "/exit":
                        break
                    elif data.get("text"):
                        await self.redis_client.publish('chat_channel', json.dumps(data))
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    break
        finally:
            # Remove the WebSocket connection from the list of clients
            if user_id:
                del self.clients[user_id]
                await self.redis_client.delete(f"user:{user_id}:{session_id}")
                print(f"{user_id} 연결 해제 및 세션 삭제 완료. (세션: {session_id})")
        return ws

    async def redis_subscriber(self):
        # Subscribe to the chat_channel in Redis to broadcast messages
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe('chat_channel')

        async for message in pubsub.listen():
            if message['type'] == 'message' and message['data']:
                try:
                    data = json.loads(message['data'])
                    if data.get('text') and data['text'].strip():
                        sender = data.get("sender", "unknown")
                        for user_id, ws in self.clients.items():
                            if sender != user_id:
                                await ws.send_json(data)
                except json.JSONDecodeError:
                    print("잘못된 메시지 포맷 감지")


if __name__ == "__main__":
    server = WebServer()
    web.run_app(server.create_app(), host="0.0.0.0", port=8080)
