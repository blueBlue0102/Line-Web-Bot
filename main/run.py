import os
import sys
from linebot import LineBot

if __name__ == "__main__":
    shutdownSeconds = int(os.environ.get("SHUTDOWN_SECONDS", 10 * 60))
    lineBot = LineBot()
    lineBot.scanChatList()
    lineBot.sseChatList(shutdownSeconds)
    sys.exit()
