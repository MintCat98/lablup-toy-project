import asyncio
import aiohttp
import redis.asyncio as redis


async def chat_client():
    # Init
    redis_client = redis.Redis(host="localhost", port=6379)

    # Username will be handled in "static/main.js"

    async with aiohttp.ClientSession() as session:
        # WebSocket connection
        async with session.ws_connect("http://localhost:8080/ws") as ws:
            print("연결 성공")

            # Send
            # To exit, click the exit button in the web page
            async def pub_to_redis():
                while True:
                    msg = input()
                    if msg.strip():  # Send only if message is not empty
                        # Exit
                        if msg.lower() == "/exit":
                            await ws.send_json({"sender": user_id, "message": "exit"})
                            await ws.close()
                            print("채팅 종료")
                            break

                        # Publish to Redis
                        await redis_client.publish("chat_channel", f"{user_id}: {msg}")
                        await ws.send_json({"sender": user_id, "message": msg})

            # Receive
            async def sub_from_redis():
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = msg.json()
                        print(f"{data['sender']}: {data['message']}")
                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        print("연결 종료")
                        break
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print("WS 에러 발생")
                        break

            await asyncio.gather(pub_to_redis(), sub_from_redis())

    await redis_client.close()


asyncio.run(chat_client())
