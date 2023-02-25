import aiohttp
import json
import time
import http.client
import random
import string
import sys
import os


class LineClient:
    def __init__(self):
        self.email = os.environ["LINE_ACCOUNT_EMAIL"]
        self.password = os.environ["LINE_ACCOUNT_PASSWORD"]
        self.mid = os.environ["LINE_ACCOUNT_MID"]
        self.defaultHeaders = {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate",
            "accept-language": "en-US,en;q=0.9",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36",
        }
        self.session = aiohttp.ClientSession()
        self.tempData = {}

    async def asyncInit(self):
        await self.loginWithEmail()

    async def loginWithEmail(self):
        """
        根據環境參數所設定的 email 和密碼進行 Line 帳號的登入
        """
        response = await self.session.get(
            url="https://account.line.biz/login?redirectUri=https%3A%2F%2Fchat.line.biz%2F",
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
                "Host": "account.line.biz",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36",
            },
            data=None,
            allow_redirects=True,
        )
        csrfToken = (await response.text()).split('name="x-csrf" content="')[1].split('"')[0]

        loginResult = await self.session.post(
            url="https://account.line.biz/api/login/email",
            headers={
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "max-age=0",
                "Connection": "keep-alive",
                "Content-Type": "application/json;charset=UTF-8",
                "Host": "account.line.biz",
                "Origin": "https://account.line.biz",
                "Referer": "https://account.line.biz/login?redirectUri=https%3A%2F%2Fchat.line.biz%2F",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36",
                "X-XSRF-TOKEN": csrfToken,
            },
            json={"email": self.email, "password": self.password, "stayLoggedIn": False},
        )
        if loginResult.status != 200:
            sys.exit(f"Login Failed, Status Code: {loginResult.status}, Error: {loginResult.text}")

        # accessToken = loginResult.headers["Set-Cookie"].split(";")[0].replace("ses=", "")

        await self.getCsrfToken()

        # TODO: 應該要檢查 chatMode，欄位變成是 "current"
        # check = self.getChatMode()
        # if 'code' in check:
        #     print("[ ERROR ] Please set bot to chat mode!!!")
        #     sys.exit()
        print("[ NOTIF ] Success login...")

    async def getCsrfToken(self):
        response = await self.session.get(
            url="https://chat.line.biz/api/v1/csrfToken",
            headers=self.defaultHeaders,
            data=None,
            allow_redirects=True,
        )
        _csrf = json.loads(await response.text())["token"]
        self.defaultHeaders["x-xsrf-token"] = _csrf

    async def getChatMode(self):
        response = await self.session.get(
            url="https://chat.line.biz/api/v3/bots/" + self.mid + "/settings/chatMode",
            headers=self.defaultHeaders,
            data=None,
            allow_redirects=True,
        )
        return json.loads(await response.text())

    async def getOwners(self):
        response = await self.session.get(
            url="https://chat.line.biz/api/v1/bots/" + self.mid + "/owners",
            headers=self.defaultHeaders,
            data=None,
            allow_redirects=True,
        )
        return json.loads(await response.text())["list"]

    async def getBots(self):
        response = await self.session.get(
            url="https://chat.line.biz/api/v1/bots?noFilter=true&limit=1000",
            headers=self.defaultHeaders,
            data=None,
            allow_redirects=True,
        )
        return json.loads(await response.text())["list"]

    async def getMessages(self, chatId):
        """
        取得對話事件（送出訊息、收到訊息或已讀等等都是一種事件） \n
        預設顯示 50 筆事件
        """
        response = await self.session.get(
            url="https://chat.line.biz/api/v2/bots/" + self.mid + "/messages/" + chatId,
            headers=self.defaultHeaders,
            data=None,
            allow_redirects=True,
        )
        return json.loads(await response.text())["list"]

    async def getImageMessages(self, chatId):
        response = await self.session.get(
            url="https://chat.line.biz/api/v1/bots/" + self.mid + "/messages/" + chatId + "/swipeViewer",
            headers=self.defaultHeaders,
            data=None,
            allow_redirects=True,
        )
        return json.loads(await response.text())["list"]

    async def getMediaInfo(self, messageId):
        response = await self.session.get(
            url="https://chat.line.biz/api/v1/bots/" + self.mid + "/messages/content/" + messageId + "/info",
            headers=self.defaultHeaders,
            data=None,
            allow_redirects=True,
        )
        return json.loads(await response.text())

    async def getChat(self, chatId):
        """
        取得關於此 chatId 的詳細資訊 \n
        例如是否已讀、名稱、狀態等等
        """
        response = await self.session.get(
            url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId,
            headers=self.defaultHeaders,
            data=None,
            allow_redirects=True,
        )
        return json.loads(await response.text())

    async def getChatList(self, folderType="ALL"):  # ['NONE', 'ALL', 'INBOX', 'UNREAD', 'FOLLOW_UP', 'DONE', 'SPAM']
        """
        `folderType = 'NONE', 'ALL', 'INBOX', 'UNREAD', 'FOLLOW_UP', 'DONE', 'SPAM'`\n
        取得 25 筆聊天
        """
        response = await self.session.get(
            url="https://chat.line.biz/api/v2/bots/" + self.mid + "/chats?folderType=" + folderType + "&tagIds=&limit=25",
            headers=self.defaultHeaders,
            data=None,
            allow_redirects=True,
        )
        return json.loads(await response.text())

    async def markAsRead(self, chatId, messageId):
        """
        將特定 chat 進行已讀 \n
        需要傳遞 messageId
        """
        data = {"messageId": messageId}
        response = await self.session.put(
            url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId + "/markAsRead",
            headers=self.defaultHeaders,
            json=data,
            allow_redirects=True,
        )
        return json.loads(await response.text())

    async def addFollowedUp(self, chatId):
        response = await self.session.put(
            url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId + "/followUp",
            headers=self.defaultHeaders,
            data=None,
            allow_redirects=True,
        )
        return json.loads(await response.text())

    async def deleteFollowedUp(self, chatId):
        response = await self.session.delete(
            url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId + "/followUp",
            headers=self.defaultHeaders,
            data=None,
            allow_redirects=True,
        )
        return json.loads(await response.text())

    async def addResolved(self, chatId):
        response = await self.session.put(
            url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId + "/done",
            headers=self.defaultHeaders,
            data=None,
            allow_redirects=True,
        )
        return json.loads(await response.text())

    async def deleteResolved(self, chatId):
        response = await self.session.delete(
            url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId + "/done",
            headers=self.defaultHeaders,
            data=None,
            allow_redirects=True,
        )
        return json.loads(await response.text())

    async def addSpam(self, chatId):
        response = await self.session.put(
            url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId + "/spam",
            headers=self.defaultHeaders,
            data=None,
            allow_redirects=True,
        )
        return json.loads(await response.text())

    async def deleteSpam(self, chatId):
        response = await self.session.delete(
            url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId + "/spam",
            headers=self.defaultHeaders,
            data=None,
            allow_redirects=True,
        )
        return json.loads(await response.text())

    async def getManualChatStatus(self, chatId):
        response = await self.session.get(
            url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId + "/useManualChat",
            headers=self.defaultHeaders,
            data=None,
            allow_redirects=True,
        )
        return json.loads(await response.text())

    async def leaveChat(self, chatId):
        response = await self.session.post(
            url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId + "/leave",
            headers=self.defaultHeaders,
            data=None,
            allow_redirects=True,
        )
        return json.loads(await response.text())

    async def deleteChat(self, chatId):
        response = await self.session.delete(
            url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId,
            headers=self.defaultHeaders,
            data=None,
            allow_redirects=True,
        )
        return json.loads(await response.text())

    async def getContactList(self):
        response = await self.session.get(
            url="https://chat.line.biz/api/v1/bots/"
            + self.mid
            + "/contacts?query=&sortKey=DISPLAY_NAME&sortOrder=ASC&excludeSpam=true&limit=100",
            headers=self.defaultHeaders,
            data=None,
            allow_redirects=True,
        )
        return json.loads(await response.text())["list"]

    async def getMembersOfChat(self, chatId):
        response = await self.session.get(
            url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId + "/members?limit=100",
            headers=self.defaultHeaders,
            data=None,
            allow_redirects=True,
        )
        return json.loads(await response.text())["list"]

    async def sendMessage(self, chatId, text):
        data = {
            "type": "text",
            "text": text,
            "sendId": chatId + "_" + str(int(time.time())) + "_" + "".join(random.choice(string.digits) for i in range(8)),
        }
        response = await self.session.post(
            url="https://chat.line.biz/api/v1/bots/" + self.mid + "/messages/" + chatId + "/send",
            headers=self.defaultHeaders,
            json=data,
            allow_redirects=True,
        )
        return json.loads(await response.text())

    async def sendSticker(self, chatId, packageId, stickerId):
        data = {
            "stickerId": stickerId,
            "packageId": packageId,
            "type": "sticker",
            "sendId": chatId + "_" + str(int(time.time())) + "_" + "".join(random.choice(string.digits) for i in range(8)),
        }
        response = await self.session.post(
            url="https://chat.line.biz/api/v1/bots/" + self.mid + "/messages/" + chatId + "/send",
            headers=self.defaultHeaders,
            json=data,
            allow_redirects=True,
        )
        return json.loads(await response.text())

    async def sendFileWithPath(self, chatId, path):
        data = {
            "file": open(path, "rb"),
            "sendId": (
                None,
                chatId + "_" + str(int(time.time())) + "_" + "".join(random.choice(string.digits) for i in range(8)),
            ),
        }
        response = await self.session.post(
            url="https://chat.line.biz/api/v1/bots/" + self.mid + "/messages/" + chatId + "/sendFile",
            headers=self.defaultHeaders,
            files=data,
            allow_redirects=True,
        )
        return json.loads(await response.text())

    async def generateContentHashUrl(self, contentHash):
        return "https://chat-content.line-scdn.net/bot/" + self.mid + "/" + contentHash

    async def streamingApiToken(self):
        response = await self.session.post(
            url="https://chat.line.biz/api/v1/bots/" + self.mid + "/streamingApiToken",
            headers=self.defaultHeaders,
            data=None,
            allow_redirects=True,
        )
        return json.loads(await response.text())

    async def openPolling(self, ping=60):
        dataStream = await self.streamingApiToken()
        streamingApiToken = dataStream["streamingApiToken"]
        lastEventId = dataStream["lastEventId"]
        # lastEventTimestamp = dataStream["lastEventTimestamp"]
        poll = http.client.HTTPSConnection("chat-streaming-api.line.biz")
        poll.request(
            "GET",
            "/api/v1/sse?token="
            + streamingApiToken
            + "&deviceToken=&deviceType=&clientType=PC&pingSecs="
            + str(ping)
            + "&lastEventId="
            + lastEventId,
            headers=self.defaultHeaders,
        )
        return poll

    async def changeNickname(self, chatId: str, nickname: str):
        """
        更改使用者的 nickname
        """
        payload = {"nickname": nickname}
        response = await self.session.put(
            url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId + "/nickname",
            headers=self.defaultHeaders,
            json=payload,
            allow_redirects=True,
        )
        return json.loads(await response.text())

    async def pinMessage(self, chatId: str, messageId: str):
        """
        釘選特定訊息
        """
        payload = {"messageId": messageId}
        await self.session.post(
            url="https://chat.line.biz/api/v1/bots/" + self.mid + "/messages/" + chatId + "/pin",
            headers=self.defaultHeaders,
            json=payload,
            allow_redirects=True,
        )
        return

    async def unpinMessage(self, chatId: str, messageId: str):
        """
        取消釘選特定訊息
        """
        payload = {"messageId": messageId}
        await self.session.delete(
            url="https://chat.line.biz/api/v1/bots/" + self.mid + "/messages/" + chatId + "/pin",
            headers=self.defaultHeaders,
            json=payload,
            allow_redirects=True,
        )
        return

    async def getPinnedMessage(self, chatId: str):
        """
        取得所有釘選中的訊息
        """
        response = await self.session.get(
            url="https://chat.line.biz/api/v2/bots/" + self.mid + "/messages/" + chatId + "/pin",
            headers=self.defaultHeaders,
            data=None,
            allow_redirects=True,
        )
        return json.loads(await response.text())["messages"]

    async def close(self):
        await self.session.close()
        return
