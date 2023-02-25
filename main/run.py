import os
import sys
import asyncio
from aiohttp import web
from hikingGuardBot import HikingGuardBot

# TODO: 任何外部服務的叫用，都應設計失敗時的處理機制
# TODO: 要假設 Line 的 API 所回傳的 Data Type 可能改變


def startWebServer():
    """
    Start a web server for health check
    """

    async def healthCheck(request):
        global hikingGuardBotIsAlive
        if hikingGuardBotIsAlive:
            return web.Response(text="Hello, world")
        else:
            sys.exit("Bot")

    server = web.Application()
    server.add_routes([web.get("/", healthCheck)])

    web.run_app(server, port=8080, shutdown_timeout=3)


async def startHikingGuardBot(SSEshutdownSeconds=10 * 60):
    """
    啟動 Hiking Guard 聊天機器人
    """
    isFirstStartUp = True
    bot = HikingGuardBot()
    while True:
        try:
            await bot.asyncInit(isFirstStartUp)
            isFirstStartUp = False

            await bot.scanChatList()
            await bot.sseChatList(SSEshutdownSeconds)
        except Exception as e:
            print(f"An Error Raise: {e}")
            global hikingGuardBotIsAlive
            hikingGuardBotIsAlive = False
            raise e


async def main():
    async with asyncio.TaskGroup() as taskGroup:
        webServerTask = taskGroup.create_task(asyncio.to_thread(startWebServer))
        hikingGuardTask = taskGroup.create_task(startHikingGuardBot(SSEshutdownSeconds))


if __name__ == "__main__":
    SSEshutdownSeconds = int(os.environ.get("SSE_SHUTDOWN_SECONDS", 10 * 60))
    global hikingGuardBotIsAlive
    hikingGuardBotIsAlive = True
    asyncio.run(main())
