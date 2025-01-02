import asyncio
import json
import aiohttp
from aiohttp import web
import redis.asyncio as redis
from aiohttp_session import get_session, new_session, setup
from aiohttp_session.redis_storage import RedisStorage
import pathlib

# Redis setting
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
clients = {}

# 프로젝트 경로 설정
BASE_DIR = pathlib.Path(__file__).parent

# Redis 연결 초기화


async def init_redis():
    redis_pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT)
    return redis.StrictRedis(connection_pool=redis_pool)


async def create_app():
    app = web.Application()

    redis_instance = await init_redis()
    setup(app, RedisStorage(redis_instance))

    # 웹 소켓 및 정적 파일 라우팅
    app.router.add_get('/ws', websocket_handler)
    app.router.add_get('/', index)
    app.router.add_static('/static/', path=BASE_DIR / 'static', name='static')

    loop = asyncio.get_event_loop()
    loop.create_task(redis_subscriber())

    return app


# Decorator for WebSocket handler
def with_session_and_redis(func):
    async def wrapper(request):
        session = await get_session(request)
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        return await func(request, ws, session)
    return wrapper


# Index handler (index.html 반환)
async def index(request):
    return web.FileResponse(BASE_DIR / 'templates/index.html')


# WebSocket handler
@with_session_and_redis
async def websocket_handler(request, ws, session):
    pubsub = redis_client.pubsub()

    user_id = session.get('user_id')
    if not user_id:
        await ws.send_json({"error": "닉네임이 없습니다. 새로고침 후 다시 시도하세요."})
        await ws.close()
        return ws

    clients[user_id] = ws
    await pubsub.subscribe('chat_channel')
    print(f"{user_id} 연결됨.")

    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)

                # 닉네임 초기 등록
                if data.get("message") == "connect":
                    session['user_id'] = data["sender"]
                    await new_session(request)
                    print(f"{user_id} 세션 등록 완료.")

                # 메시지 중계
                elif data.get("message") == "/exit":
                    print(f"{user_id} 채팅 종료.")
                    break
                else:
                    await redis_client.publish('chat_channel', json.dumps(data))
            elif msg.type == aiohttp.WSMsgType.CLOSED:
                break
    finally:
        if user_id and user_id in clients:
            del clients[user_id]
        await pubsub.unsubscribe('chat_channel')
        await ws.close()
        print(f"{user_id} 연결 종료")
    return ws


# Redis Pub/Sub subscriber
async def redis_subscriber():
    pubsub = redis_client.pubsub()
    await pubsub.subscribe('chat_channel')

    async for message in pubsub.listen():
        if message['type'] == 'message':
            data = json.loads(message['data'])
            sender = data.get("sender")
            for user_id, ws in clients.items():
                if sender != user_id:  # 발신자 제외
                    await ws.send_json(data)


# Run server
if __name__ == "__main__":
    web.run_app(create_app(), port=8080)
