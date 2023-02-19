import os
import asyncio
from aiohttp import web
from hikingGuardBot import HikingGuardBot

# TODO: 任何外部服務的叫用，都應設計失敗時的處理機制
# TODO: 要假設 Line 的 API 所回傳的 Data Type 可能改變


async def startWebServer():
    """
    Start a web server for health check
    """

    async def hello(request):
        return web.Response(text="Hello, world")

    server = web.Application()
    server.add_routes([web.get("/", hello)])
    runner = web.AppRunner(server)
    await runner.setup()
    await web.TCPSite(runner, "localhost", 8080).start()


async def startHikingGuardBot(SSEshutdownSeconds=10 * 60):
    """
    啟動 Hiking Guard 聊天機器人
    """
    while True:
        bot = HikingGuardBot()
        await bot.asyncInit()
        await bot.scanChatList()
        await bot.sseChatList(SSEshutdownSeconds)


if __name__ == "__main__":
    SSEshutdownSeconds = int(os.environ.get("SSE_SHUTDOWN_SECONDS", 10 * 60))
    loop = asyncio.get_event_loop_policy().get_event_loop()
    loop.create_task(startWebServer())
    loop.create_task(startHikingGuardBot())
    loop.run_forever()
