import asyncio
import aiohttp
import redis.asyncio as redis


async def chat_client():
    redis_client = redis.Redis(host="redis", port=6379)

    user_id = await redis_client.get("user:current_user")

    if not user_id:
        print("닉네임이 없습니다. 먼저 웹에서 닉네임을 설정하세요.")
        return

    user_id = user_id.decode("utf-8")
    print(f"{user_id}으로 연결 시도 중...")

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect("http://redis:8080/ws") as ws:
            print(f"{user_id}으로 연결 성공")

            async def pub_to_redis():
                while True:
                    msg = input("메시지: ").strip()
                    if msg:
                        if msg.lower() == "/exit":
                            await ws.send_json({"sender": user_id, "message": "exit"})
                            await ws.close()
                            print("채팅 종료")
                            break
                        await redis_client.publish("chat_channel", f"{user_id}: {msg}")
                        await ws.send_json({"sender": user_id, "text": msg})

            async def sub_from_redis():
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = msg.json()
                        print(f"{data['sender']}: {data['text']}")
                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        print("연결 종료")
                        break
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print("WebSocket 에러 발생")
                        break

            await asyncio.gather(pub_to_redis(), sub_from_redis())

    await redis_client.close()


asyncio.run(chat_client())
