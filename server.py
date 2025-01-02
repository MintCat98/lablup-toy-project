import asyncio
import json
import aiohttp
from aiohttp import web
import redis.asyncio as redis
from aiohttp_session import get_session, setup
from aiohttp_session.redis_storage import RedisStorage
import pathlib

# Redis 설정
REDIS_HOST = 'redis'
REDIS_PORT = 6379
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
clients = {}

# 프로젝트 경로 설정
BASE_DIR = pathlib.Path(__file__).parent


async def init_redis():
    redis_pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT)
    return redis.StrictRedis(connection_pool=redis_pool)


async def create_app():
    app = web.Application()

    redis_instance = await init_redis()
    setup(app, RedisStorage(redis_instance))

    # 웹 소켓 및 정적 파일 라우팅
    app.router.add_get('/ws', websocket_handler)
    app.router.add_post('/set-nickname', set_nickname)
    app.router.add_get('/', index)
    app.router.add_static('/static/', path=BASE_DIR / 'static', name='static')

    loop = asyncio.get_event_loop()
    loop.create_task(redis_subscriber())

    return app


# 닉네임 설정 핸들러
async def set_nickname(request):
    data = await request.json()
    nickname = data.get('nickname')
    session = await get_session(request)
    session['user_id'] = nickname
    return web.json_response({'message': f'{nickname} 닉네임 설정 완료'})


# WebSocket 핸들러
def with_session_and_redis(func):
    async def wrapper(request):
        session = await get_session(request)
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        return await func(request, ws, session)
    return wrapper


async def index(request):
    session = await get_session(request)
    user_id = session.get('user_id', '닉네임 없음')
    print(f"현재 세션 사용자: {user_id}")
    return web.FileResponse(BASE_DIR / 'templates/index.html')


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

    # 입장 메시지 브로드캐스트
    join_message = {"sender": "system", "text": f"{user_id} 님이 입장하셨습니다."}
    await redis_client.publish('chat_channel', json.dumps(join_message))

    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)

                if data.get("message") == "connect":
                    user_id = data["sender"]
                    session['user_id'] = user_id
                    await ws.send_json({"message": f"{user_id} 닉네임 저장 완료"})
                    print(f"닉네임 {user_id} 세션에 저장 완료.")

                elif data.get("message") == "/exit":
                    print(f"{user_id} 채팅 종료.")
                    break

                elif data.get("text") and data['text'].strip():
                    await redis_client.publish('chat_channel', json.dumps(data))

            elif msg.type == aiohttp.WSMsgType.CLOSED:
                break
    finally:
        if user_id and user_id in clients:
            del clients[user_id]
    return ws


# Redis Pub/Sub 구독자
async def redis_subscriber():
    pubsub = redis_client.pubsub()
    await pubsub.subscribe('chat_channel')

    async for message in pubsub.listen():
        if message['type'] == 'message' and message['data']:
            try:
                data = json.loads(message['data'])
                if data.get('text') and data['text'].strip():
                    sender = data.get("sender", "unknown")
                    for user_id, ws in clients.items():
                        if sender != user_id:
                            await ws.send_json(data)
            except json.JSONDecodeError:
                print("잘못된 메시지 포맷 감지")


# 서버 실행
if __name__ == "__main__":
    web.run_app(create_app(), host="0.0.0.0", port=8080)
