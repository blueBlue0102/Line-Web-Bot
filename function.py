import requests
import json
import time
import http.client
import random
import string
import sys
import os

lineCredentialPath = os.path.join("secrets", "line-credential.json")


class Client:
    def __init__(self):
        self.defaultHeaders = {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate",
            "accept-language": "en-US,en;q=0.9",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36",
        }
        self.session = requests.session()
        self.tempData = {}
        self.loadSession()

    def readJson(self, filename):
        if not os.path.exists(filename):
            self.writeJson(filename, {})
        with open(filename) as f:
            return json.load(f)

    def writeJson(self, filename, data):
        with open(filename, "w") as f:
            json.dump(data, f, indent=4, sort_keys=True)

    def loadSession(self):
        """
        讀取特定路徑下的 Line 憑證 \n
        若憑證不存在，則報錯誤
        若憑證存在，但是驗證後發現過期，報錯誤
        """
        credential = self.readJson(lineCredentialPath)

        if not all(
            credKey in credential
            for credKey in [
                "authToken",
                "mid",
                "userId",
            ]
        ):
            sys.exit("Certificate verification failed, please log in again.")

        self.session.cookies.set("ses", credential["authToken"])
        self.mid = credential["mid"]
        self.userId = credential["userId"]
        checkLogin = json.loads(
            self.session.get(
                url="https://chat.line.biz/api/v1/bots?noFilter=true&limit=1000",
                headers=self.defaultHeaders,
                data=None,
                allow_redirects=True,
            ).text
        )
        if "code" in checkLogin:
            sys.exit(f'Certificate verification failed, please log in again. Code: {checkLogin["code"]}')

        self.getCsrfToken()

        # TODO: 應該要檢查 chatMode，欄位變成是 "current"
        # check = self.getChatMode()
        # if 'code' in check:
        #     print("[ ERROR ] Please set bot to chat mode!!!")
        #     sys.exit()
        print("[ NOTIF ] Success login...")

    def getCsrfToken(self):
        _csrf = json.loads(
            self.session.get(
                url="https://chat.line.biz/api/v1/csrfToken",
                headers=self.defaultHeaders,
                data=None,
                allow_redirects=True,
            ).text
        )["token"]
        self.defaultHeaders["x-xsrf-token"] = _csrf

    def getChatMode(self):
        return json.loads(
            self.session.get(
                url="https://chat.line.biz/api/v3/bots/" + self.mid + "/settings/chatMode",
                headers=self.defaultHeaders,
                data=None,
                allow_redirects=True,
            ).text
        )

    def getOwners(self):
        return json.loads(
            self.session.get(
                url="https://chat.line.biz/api/v1/bots/" + self.mid + "/owners",
                headers=self.defaultHeaders,
                data=None,
                allow_redirects=True,
            ).text
        )["list"]

    def getBots(self):
        return json.loads(
            self.session.get(
                url="https://chat.line.biz/api/v1/bots?noFilter=true&limit=1000",
                headers=self.defaultHeaders,
                data=None,
                allow_redirects=True,
            ).text
        )["list"]

    def getMessages(self, chatId):
        """
        取得對話事件（送出訊息、收到訊息或已讀等等都是一種事件） \n
        預設顯示 50 筆事件
        """
        return json.loads(
            self.session.get(
                url="https://chat.line.biz/api/v1/bots/" + self.mid + "/messages/" + chatId,
                headers=self.defaultHeaders,
                data=None,
                allow_redirects=True,
            ).text
        )["list"]

    def getImageMessages(self, chatId):
        return json.loads(
            self.session.get(
                url="https://chat.line.biz/api/v1/bots/" + self.mid + "/messages/" + chatId + "/swipeViewer",
                headers=self.defaultHeaders,
                data=None,
                allow_redirects=True,
            ).text
        )["list"]

    def getMediaInfo(self, messageId):
        return json.loads(
            self.session.get(
                url="https://chat.line.biz/api/v1/bots/" + self.mid + "/messages/content/" + messageId + "/info",
                headers=self.defaultHeaders,
                data=None,
                allow_redirects=True,
            ).text
        )

    def getChat(self, chatId):
        """
        取得關於此 chatId 的詳細資訊 \n
        例如是否已讀、名稱、狀態等等
        """
        return json.loads(
            self.session.get(
                url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId,
                headers=self.defaultHeaders,
                data=None,
                allow_redirects=True,
            ).text
        )

    def getChatList(self, folderType="ALL"):  # ['NONE', 'ALL', 'INBOX', 'UNREAD', 'FOLLOW_UP', 'DONE', 'SPAM']
        return json.loads(
            self.session.get(
                url="https://chat.line.biz/api/v2/bots/"
                + self.mid
                + "/chats?folderType="
                + folderType
                + "&tagIds=&limit=25",
                headers=self.defaultHeaders,
                data=None,
                allow_redirects=True,
            ).text
        )

    def markAsRead(self, chatId, messageId):
        """
        將特定 chat 進行已讀 \n
        需要傳遞 messageId
        """
        data = {"messageId": messageId}
        return json.loads(
            self.session.put(
                url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId + "/markAsRead",
                headers=self.defaultHeaders,
                json=data,
                allow_redirects=True,
            ).text
        )

    def addFollowedUp(self, chatId):
        return json.loads(
            self.session.put(
                url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId + "/followUp",
                headers=self.defaultHeaders,
                data=None,
                allow_redirects=True,
            ).text
        )

    def deleteFollowedUp(self, chatId):
        return json.loads(
            self.session.delete(
                url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId + "/followUp",
                headers=self.defaultHeaders,
                data=None,
                allow_redirects=True,
            ).text
        )

    def addResolved(self, chatId):
        return json.loads(
            self.session.put(
                url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId + "/done",
                headers=self.defaultHeaders,
                data=None,
                allow_redirects=True,
            ).text
        )

    def deleteResolved(self, chatId):
        return json.loads(
            self.session.delete(
                url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId + "/done",
                headers=self.defaultHeaders,
                data=None,
                allow_redirects=True,
            ).text
        )

    def addSpam(self, chatId):
        return json.loads(
            self.session.put(
                url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId + "/spam",
                headers=self.defaultHeaders,
                data=None,
                allow_redirects=True,
            ).text
        )

    def deleteSpam(self, chatId):
        return json.loads(
            self.session.delete(
                url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId + "/spam",
                headers=self.defaultHeaders,
                data=None,
                allow_redirects=True,
            ).text
        )

    def getManualChatStatus(self, chatId):
        return json.loads(
            self.session.get(
                url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId + "/useManualChat",
                headers=self.defaultHeaders,
                data=None,
                allow_redirects=True,
            ).text
        )

    def leaveChat(self, chatId):
        return json.loads(
            self.session.post(
                url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId + "/leave",
                headers=self.defaultHeaders,
                data=None,
                allow_redirects=True,
            ).text
        )

    def deleteChat(self, chatId):
        return json.loads(
            self.session.delete(
                url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId,
                headers=self.defaultHeaders,
                data=None,
                allow_redirects=True,
            ).text
        )

    def getContactList(self):
        return json.loads(
            self.session.get(
                url="https://chat.line.biz/api/v1/bots/"
                + self.mid
                + "/contacts?query=&sortKey=DISPLAY_NAME&sortOrder=ASC&excludeSpam=true&limit=100",
                headers=self.defaultHeaders,
                data=None,
                allow_redirects=True,
            ).text
        )["list"]

    def getMembersOfChat(self, chatId):
        return json.loads(
            self.session.get(
                url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId + "/members?limit=100",
                headers=self.defaultHeaders,
                data=None,
                allow_redirects=True,
            ).text
        )["list"]

    def sendMessage(self, chatId, text):
        data = {
            "type": "text",
            "text": text,
            "sendId": chatId + "_" + str(int(time.time())) + "_" + "".join(random.choice(string.digits) for i in range(8)),
        }
        return json.loads(
            self.session.post(
                url="https://chat.line.biz/api/v1/bots/" + self.mid + "/messages/" + chatId + "/send",
                headers=self.defaultHeaders,
                json=data,
                allow_redirects=True,
            ).text
        )

    def sendSticker(self, chatId, packageId, stickerId):
        data = {
            "stickerId": stickerId,
            "packageId": packageId,
            "type": "sticker",
            "sendId": chatId + "_" + str(int(time.time())) + "_" + "".join(random.choice(string.digits) for i in range(8)),
        }
        return json.loads(
            self.session.post(
                url="https://chat.line.biz/api/v1/bots/" + self.mid + "/messages/" + chatId + "/send",
                headers=self.defaultHeaders,
                json=data,
                allow_redirects=True,
            ).text
        )

    def sendFileWithPath(self, chatId, path):
        data = {
            "file": open(path, "rb"),
            "sendId": (
                None,
                chatId + "_" + str(int(time.time())) + "_" + "".join(random.choice(string.digits) for i in range(8)),
            ),
        }
        return json.loads(
            self.session.post(
                url="https://chat.line.biz/api/v1/bots/" + self.mid + "/messages/" + chatId + "/sendFile",
                headers=self.defaultHeaders,
                files=data,
                allow_redirects=True,
            ).text
        )

    def generateContentHashUrl(self, contentHash):
        return "https://chat-content.line-scdn.net/bot/" + self.mid + "/" + contentHash

    def streamingApiToken(self):
        return json.loads(
            self.session.post(
                url="https://chat.line.biz/api/v1/bots/" + self.mid + "/streamingApiToken",
                headers=self.defaultHeaders,
                data=None,
                allow_redirects=True,
            ).text
        )

    def openPolling(self, ping=60):
        dataStream = self.streamingApiToken()
        streamingApiToken = dataStream["streamingApiToken"]
        lastEventId = dataStream["lastEventId"]
        lastEventTimestamp = dataStream["lastEventTimestamp"]
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

    def changeNickname(self, chatId: str, nickname: str):
        """
        更改使用者的 nickname
        """
        data = {"nickname": nickname}
        return json.loads(
            self.session.put(
                url="https://chat.line.biz/api/v1/bots/" + self.mid + "/chats/" + chatId + "/nickname",
                headers=self.defaultHeaders,
                json=data,
                allow_redirects=True,
            ).text
        )
