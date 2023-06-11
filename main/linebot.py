import re
import sys
import time
import json
from datetime import datetime, timedelta
from lineClient import LineClient
from firebaseClient import FirebaseClient


class LineBot:
    def __init__(self) -> None:
        self.lineClient = LineClient()
        self.firebaseClient = FirebaseClient()

    def __startTrip(self, chatId: str, tripId: str, username: str, isGroup=False):
        """
        「建立行程」的處理邏輯
        """

        # 在 firebase 中進行尋找對應的行程
        tripData = self.firebaseClient.getTrip(tripId)
        if tripData is None:
            # 沒找到
            self.lineClient.sendMessage(chatId, (f"很抱歉，沒有找到對應的行程代碼（{tripId}）\n" "請確認代碼沒有輸入錯誤，或是再試一次"))
            return

        # 找到了，開始執行動作
        # 發送行程資訊
        inDatetime = datetime.strptime(tripData["inDatetime"], "%Y-%m-%dT%H:%M:%S.%fZ") + timedelta(hours=8)
        outDatetime = datetime.strptime(tripData["outDatetime"], "%Y-%m-%dT%H:%M:%S.%fZ") + timedelta(hours=8)
        message = (
            f"【留守管理員通知頻道 - 旅程建立成功】\n"
            f"收到以下行程：\n"
            f"旅程 [{tripId}] 建立成功\n"
            f'名稱：{tripData["pathName"]}\n'
            f"入時：{inDatetime} (GMT+8)\n"
            f"出時：{outDatetime} (GMT+8)\n"
            f'行程內容：\n{tripData["pathDetail"]}\n\n'
            f'▲ 延遲 {tripData["delayHour"]} 小時通報'
        )
        self.lineClient.sendMessage(chatId, message)

        # 發送行程提醒
        message = "已收到行程申請，提醒您，出發前回傳「登山當天的衣著」與「攜帶裝備之照片或清單」，才算完成申請程序，並於出發時回覆「啟動留守」後才會進行留守服務唷！"
        self.lineClient.sendMessage(chatId, message)

        # 更改暱稱
        nPathDate = (
            f"{inDatetime.month}/{inDatetime.day}"
            if inDatetime.day == outDatetime.day
            else f"{inDatetime.month}/{inDatetime.day}-{outDatetime.day}"
        )
        nOutDateTime = f"{outDatetime.hour}{outDatetime.minute}"
        nDelayHour = f"+{tripData['delayHour']}"

        nUserName = ""
        nPathName = ""
        othersLength = len(nPathDate + nOutDateTime + nDelayHour)
        if isGroup is True:
            ## 對話是群組
            ### pathname: 全部放，但須注意要保留至少兩個字元給 username
            ### username: 能放多少就放多少
            nPathName = tripData["pathName"][0 : 48 - othersLength]
            nUserName = username[0 : 50 - othersLength - len(nPathName)]
        else:
            ## 對話是個人
            ### username: 只保留 2 個字元
            ### pathname: 全部保留直到到達 20 個字元
            nUserName = username[0:2]
            nPathName = tripData["pathName"][0 : 20 - othersLength - len(nUserName)]

        self.lineClient.changeNickname(
            chatId,
            (nUserName + nPathDate + nPathName + nOutDateTime + nDelayHour),
        )

        # Follow up
        self.lineClient.addFollowedUp(chatId)

        # 釘選訊息
        time.sleep(1.5)
        messageEventList = self.lineClient.getMessages(chatId)
        for messageEvent in messageEventList:
            if (
                messageEvent["type"] == "messageSent"
                and messageEvent["message"]["type"] == "text"
                and messageEvent["message"]["text"][0:20] == "【留守管理員通知頻道 - 旅程建立成功】"
            ):
                self.lineClient.pinMessage(chatId, messageEvent["message"]["id"])
                break

    def __stopTrip(self, chatId: str):
        """
        「結束行程」的處理邏輯
        """
        self.lineClient.changeNickname(chatId, "")
        self.lineClient.addResolved(chatId)
        pinnedMessageList = self.lineClient.getPinnedMessage(chatId)
        for pinnedMessage in pinnedMessageList:
            if (
                pinnedMessage["type"] == "messageSent"
                and pinnedMessage["message"]["type"] == "text"
                and pinnedMessage["message"]["text"][0:20] == "【留守管理員通知頻道 - 旅程建立成功】"
            ):
                self.lineClient.unpinMessage(chatId, pinnedMessage["message"]["id"])
                break

    def __startGuarding(self, chatId: str):
        """
        留守人開始進行留守
        """
        self.lineClient.sendMessage(chatId, "沿途有訊號時，記得回報人員狀況和座標位置喔。")

    def scanChatList(self):
        """
        抓取最多 25 個訊息 inbox 的訊息，判斷是否要建立行程
        如果是，則開始建立行程的流程
        如果不是，則忽略
        """

        def isClientSendingTextMsg(chat) -> bool:
            return chat["latestEvent"]["type"] == "message" and chat["latestEvent"]["message"]["type"] == "text"

        def isClientSendingStickerMsg(chat) -> bool:
            return chat["latestEvent"]["type"] == "message" and chat["latestEvent"]["message"]["type"] == "sticker"

        def isGuardSendingTextMsg(chat) -> bool:
            return chat["latestEvent"]["type"] == "messageSent" and chat["latestEvent"]["message"]["type"] == "text"

        def isGuardSendingStickerMsg(chat) -> bool:
            return chat["latestEvent"]["type"] == "messageSent" and chat["latestEvent"]["message"]["type"] == "sticker"

        def isTripStart(chat) -> bool:
            """
            傳送的訊息是否含有行程代碼
            """
            msg = chat["latestEvent"]["message"]["text"]
            regResult = re.search("T-[0-9]{13}-[a-zA-Z0-9]{3}", msg)
            return regResult is not None

        def isStartGuarding(chat) -> bool:
            """
            留守人宣布啟動留守
            """
            msg = chat["latestEvent"]["message"]
            if msg["type"] == "sticker":
                return msg["packageId"] == "17139130" and msg["stickerId"] == "443245260"
            elif msg["type"] == "text":
                return msg["text"] == "啟動留守" or msg["text"] == "留守啟動"

            return False

        def isGuardSendingTripId(chat) -> bool:
            """
            訊息內容是純粹的行程代碼，沒有任何多餘的字元
            """
            msg = chat["latestEvent"]["message"]["text"]
            if len(msg) != 19:
                return False
            regResult = re.search("T-[0-9]{13}-[a-zA-Z0-9]{3}", msg)
            if regResult is None:
                return False
            else:
                return True

        def getTripId(chat) -> str:
            msg = chat["latestEvent"]["message"]["text"]
            regResult = re.search("T-[0-9]{13}-[a-zA-Z0-9]{3}", msg)
            if regResult is None:
                return ""
            else:
                return regResult.group()

        def isTripStop(chat) -> bool:
            msg = chat["latestEvent"]["message"]
            if msg["type"] == "text":
                return msg["text"] == "留守結束" or msg["text"] == "結束留守"
            elif msg["type"] == "sticker":
                return msg["packageId"] == "17139130" and msg["stickerId"] == "443245261"

            return False

        def getUsername(chat) -> str:
            if chat["chatType"] == "USER":
                return chat["profile"]["name"]
            else:
                return self.lineClient.getChat(chat["chatId"])["profile"]["name"]

        def chatTypeIsGroup(chat) -> bool:
            return chat["chatType"] == "GROUP"

        chatList = self.lineClient.getChatList(folderType="INBOX")["list"]
        for chat in chatList:
            chatId = chat["chatId"]
            if chat["status"] == "blocked":
                continue
            elif isClientSendingTextMsg(chat):
                if isTripStart(chat):
                    username = getUsername(chat)
                    tripId = getTripId(chat)
                    self.__startTrip(chatId, tripId, username, chatTypeIsGroup(chat))
                    print(f"User [{username}] start a trip.")
                    time.sleep(0.25)
            elif isGuardSendingTextMsg(chat):
                if isTripStop(chat):
                    username = getUsername(chat)
                    self.__stopTrip(chatId)
                    print(f"User [{username}] stop a trip.")
                    time.sleep(0.25)
                elif isStartGuarding(chat):
                    username = getUsername(chat)
                    self.__startGuarding(chatId)
                    print(f"User [{username}] start guarding.")
                    time.sleep(0.25)
                elif isGuardSendingTripId(chat):
                    username = getUsername(chat)
                    tripId = getTripId(chat)
                    self.__startTrip(chatId, tripId, username, chatTypeIsGroup(chat))
                    print(f"User [{username}] start a trip By Guard.")
                    time.sleep(0.25)
            elif isGuardSendingStickerMsg(chat):
                if isStartGuarding(chat):
                    username = getUsername(chat)
                    self.__startGuarding(chatId)
                    print(f"User [{username}] start guarding.")
                    time.sleep(0.25)
                elif isTripStop(chat):
                    username = getUsername(chat)
                    self.__stopTrip(chatId)
                    print(f"User [{username}] stop a trip.")
                    time.sleep(0.25)

        print(f"scanChatList Finish")

    def sseChatList(self, shutdownSeconds=10 * 60):
        """
        透過 SSE 取得 Line 的即時訊息通知
        收到訊息後，依據內容執行不同行為
        """

        def isClientSendingTextMsg(chunk) -> bool:
            return (
                chunk["event"] == "chat"
                and "subEvent" in chunk
                and chunk["subEvent"] == "message"
                and chunk["payload"]["message"]["type"] == "text"
            )

        def isClientSendingStickerMsg(chunk) -> bool:
            return (
                chunk["event"] == "chat"
                and "subEvent" in chunk
                and chunk["subEvent"] == "message"
                and chunk["payload"]["message"]["type"] == "sticker"
            )

        def isGuardSendingTextMsg(chunk) -> bool:
            return (
                chunk["event"] == "chat"
                and "subEvent" in chunk
                and chunk["subEvent"] == "messageSent"
                and chunk["payload"]["message"]["type"] == "text"
            )

        def isGuardSendingStickerMsg(chunk) -> bool:
            return (
                chunk["event"] == "chat"
                and "subEvent" in chunk
                and chunk["subEvent"] == "messageSent"
                and chunk["payload"]["message"]["type"] == "sticker"
            )

        def isTripStart(chunk) -> bool:
            """
            檢測訊息內容是否含有行程代碼
            """
            msg = chunk["payload"]["message"]["text"]
            regResult = re.search("T-[0-9]{13}-[a-zA-Z0-9]{3}", msg)
            return regResult is not None

        def isStartGuarding(chunk) -> bool:
            """
            留守人宣布啟動留守
            """
            msg = chunk["payload"]["message"]
            if msg["type"] == "text":
                return msg["text"] == "啟動留守" or msg["text"] == "留守啟動"
            elif msg["type"] == "sticker":
                return msg["packageId"] == "17139130" and msg["stickerId"] == "443245260"

            return False

        def isGuardSendingTripId(chunk) -> bool:
            """
            訊息內容是純粹的行程代碼，沒有任何多餘的字元
            """
            msg = chunk["payload"]["message"]["text"]
            if len(msg) != 19:
                return False
            regResult = re.search("T-[0-9]{13}-[a-zA-Z0-9]{3}", msg)
            if regResult is None:
                return False
            else:
                return True

        def getTripId(chunk) -> str:
            msg = chunk["payload"]["message"]["text"]
            regResult = re.search("T-[0-9]{13}-[a-zA-Z0-9]{3}", msg)
            if regResult is None:
                return ""
            else:
                return regResult.group()

        def isTripStop(chunk) -> bool:
            msg = chunk["payload"]["message"]
            if msg["type"] == "text":
                return msg["text"] == "留守結束" or msg["text"] == "結束留守"
            elif msg["type"] == "sticker":
                return msg["packageId"] == "17139130" and msg["stickerId"] == "443245261"

            return False

        def isTimesUp(startTime) -> bool:
            if shutdownSeconds <= 0:
                return False
            elif (time.time() - startTime) >= shutdownSeconds:
                return True
            else:
                return False

        def chatTypeIsGroup(chatType: str) -> bool:
            return chatType == "GROUP"

        poll = self.lineClient.openPolling()
        startTime = time.time()
        with poll.getresponse() as response:
            if response.getcode() != 200:
                sys.exit(f"SSE poll HTTP status code is not 200, code: {response.getcode()}")
            while not response.closed:
                for data in response:
                    decodedData = data.decode("utf-8")
                    if "data:{" in decodedData:
                        print(f"{datetime.now()}, Received SSE Data...")
                        chunk = json.loads(decodedData.replace("data:", ""))
                        if isClientSendingTextMsg(chunk):
                            chatId = chunk["payload"]["source"]["chatId"]
                            if isTripStart(chunk):
                                tripId = getTripId(chunk)
                                chat = self.lineClient.getChat(chatId)
                                username = chat["profile"]["name"]
                                self.__startTrip(chatId, tripId, username, chatTypeIsGroup(chat["chatType"]))
                                print(f"User [{username}] start a trip.")
                        elif isGuardSendingTextMsg(chunk):
                            chatId = chunk["payload"]["source"]["chatId"]
                            username = self.lineClient.getChat(chatId)["profile"]["name"]
                            if isTripStop(chunk):
                                self.__stopTrip(chatId)
                                print(f"User [{username}] stop a trip.")
                            elif isStartGuarding(chunk):
                                self.__startGuarding(chatId)
                                print(f"User [{username}] start guarding.")
                            elif isGuardSendingTripId(chunk):
                                tripId = getTripId(chunk)
                                chat = self.lineClient.getChat(chatId)
                                username = chat["profile"]["name"]
                                self.__startTrip(chatId, tripId, username, chatTypeIsGroup(chat["chatType"]))
                                print(f"User [{username}] start a trip By Guard.")
                        elif isGuardSendingStickerMsg(chunk):
                            chatId = chunk["payload"]["source"]["chatId"]
                            username = self.lineClient.getChat(chatId)["profile"]["name"]
                            if isStartGuarding(chunk):
                                self.__startGuarding(chatId)
                                print(f"User [{username}] start guarding.")
                            elif isTripStop(chunk):
                                self.__stopTrip(chatId)
                                print(f"User [{username}] stop a trip.")
                    if isTimesUp(startTime):
                        print(f"Time's up: {shutdownSeconds} seconds.")
                        return
