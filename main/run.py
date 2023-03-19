import os
import re
import sys
import time
import json
from datetime import datetime, timedelta
from lineClient import LineClient
from firebaseClient import FirebaseClient

lineClient = LineClient()
firebaseClient = FirebaseClient()

# TODO: 任何外部服務的叫用，都應設計失敗時的處理機制
# TODO: 要假設 Line 的 API 所回傳的 Data Type 可能改變


def startTrip(chatId: str, tripId: str, username: str):
    """
    「建立行程」的處理邏輯
    """

    # 在 firebase 中進行尋找對應的行程
    tripData = firebaseClient.getTrip(tripId)
    if tripData is None:
        # 沒找到
        lineClient.sendMessage(chatId, (f"很抱歉，沒有找到對應的行程代碼（{tripId}）\n" "請確認代碼沒有輸入錯誤，或是再試一次"))
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
    lineClient.sendMessage(chatId, message)

    # 發送行程提醒
    message = "已收到行程申請，提醒您，出發前回傳「登山當天的衣著」與「攜帶裝備之照片或清單」，才算完成申請程序，並於出發時回覆「啟動留守」後才會進行留守服務唷！"
    lineClient.sendMessage(chatId, message)

    # 更改暱稱
    lineClient.changeNickname(
        chatId,
        (
            f"{username[0: 2]}"
            f"{inDatetime.month}/{inDatetime.day}-{outDatetime.day}"
            f"{tripData['pathName'][0:2]}"
            f"{outDatetime.hour}:{outDatetime.minute}"
            f"+{tripData['delayHour']}"
        ),
    )

    # Follow up
    lineClient.addFollowedUp(chatId)

    # 釘選訊息
    time.sleep(1.5)
    messageEventList = lineClient.getMessages(chatId)
    for messageEvent in messageEventList:
        if (
            messageEvent["type"] == "messageSent"
            and messageEvent["message"]["type"] == "text"
            and messageEvent["message"]["text"][0:20] == "【留守管理員通知頻道 - 旅程建立成功】"
        ):
            lineClient.pinMessage(chatId, messageEvent["message"]["id"])
            break


def stopTrip(chatId: str):
    """
    「結束行程」的處理邏輯
    """
    lineClient.changeNickname(chatId, "")
    lineClient.addResolved(chatId)
    pinnedMessageList = lineClient.getPinnedMessage(chatId)
    for pinnedMessage in pinnedMessageList:
        if (
            pinnedMessage["type"] == "messageSent"
            and pinnedMessage["message"]["type"] == "text"
            and pinnedMessage["message"]["text"][0:20] == "【留守管理員通知頻道 - 旅程建立成功】"
        ):
            lineClient.unpinMessage(chatId, pinnedMessage["message"]["id"])
            break


def startGuarding(chatId: str):
    """
    留守人開始進行留守
    """
    lineClient.sendMessage(chatId, "沿途有訊號時，記得回報人員狀況和座標位置喔。")


def scanChatList():
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
        if chat["status"] == "blocked":
            return False
        msg = chat["latestEvent"]["message"]["text"]
        regResult = re.search("T-[0-9]{13}-[a-zA-Z0-9]{3}", msg)
        return regResult is not None

    def isStartGuarding(chat) -> bool:
        """
        留守人宣布啟動留守
        """
        if chat["status"] == "blocked":
            return False

        msg = chat["latestEvent"]["message"]
        if msg["type"] == "sticker":
            return msg["packageId"] == "17139130" and msg["stickerId"] == "443245260"
        elif msg["type"] == "text":
            return msg["text"] == "啟動留守" or msg["text"] == "留守啟動"

        return False

    def getTripId(chat) -> str:
        if chat["status"] == "blocked":
            return ""
        msg = chat["latestEvent"]["message"]["text"]
        regResult = re.search("T-[0-9]{13}-[a-zA-Z0-9]{3}", msg)
        if regResult is None:
            return ""
        else:
            return regResult.group()

    def isTripStop(chat) -> bool:
        if chat["status"] == "blocked":
            return False

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
            return lineClient.getChat(chat["chatId"])["profile"]["name"]

    chatList = lineClient.getChatList(folderType="INBOX")["list"]
    for chat in chatList:
        chatId = chat["chatId"]
        if isClientSendingTextMsg(chat):
            if isTripStart(chat):
                username = getUsername(chat)
                tripId = getTripId(chat)
                startTrip(chatId, tripId, username)
                print(f"User [{username}] start a trip.")
                time.sleep(0.25)
        elif isGuardSendingTextMsg(chat):
            if isTripStop(chat):
                username = getUsername(chat)
                stopTrip(chatId)
                print(f"User [{username}] stop a trip.")
                time.sleep(0.25)
            elif isStartGuarding(chat):
                username = getUsername(chat)
                startGuarding(chatId)
                print(f"User [{username}] start guarding.")
                time.sleep(0.25)
        elif isGuardSendingStickerMsg(chat):
            if isStartGuarding(chat):
                username = getUsername(chat)
                startGuarding(chatId)
                print(f"User [{username}] start guarding.")
                time.sleep(0.25)
            elif isTripStop(chat):
                username = getUsername(chat)
                stopTrip(chatId)
                print(f"User [{username}] stop a trip.")
                time.sleep(0.25)

    print(f"scanChatList Finish")


def sseChatList(shutdownSeconds=10 * 60):
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

    poll = lineClient.openPolling()
    startTime = time.time()
    with poll.getresponse() as response:
        while not response.closed:
            for data in response:
                decodedData = data.decode("utf-8")
                if "data:{" in decodedData:
                    chunk = json.loads(decodedData.replace("data:", ""))
                    if isClientSendingTextMsg(chunk):
                        chatId = chunk["payload"]["source"]["chatId"]
                        if isTripStart(chunk):
                            tripId = getTripId(chunk)
                            username = lineClient.getChat(chatId)["profile"]["name"]
                            startTrip(chatId, tripId, username)
                            print(f"User [{username}] start a trip.")
                    elif isGuardSendingTextMsg(chunk):
                        chatId = chunk["payload"]["source"]["chatId"]
                        username = lineClient.getChat(chatId)["profile"]["name"]
                        if isTripStop(chunk):
                            stopTrip(chatId)
                            print(f"User [{username}] stop a trip.")
                        elif isStartGuarding(chunk):
                            startGuarding(chatId)
                            print(f"User [{username}] start guarding.")
                    elif isGuardSendingStickerMsg(chunk):
                        chatId = chunk["payload"]["source"]["chatId"]
                        username = lineClient.getChat(chatId)["profile"]["name"]
                        if isStartGuarding(chunk):
                            startGuarding(chatId)
                            print(f"User [{username}] start guarding.")
                        elif isTripStop(chunk):
                            stopTrip(chatId)
                            print(f"User [{username}] stop a trip.")
                if isTimesUp(startTime):
                    print(f"Time's up: {shutdownSeconds} seconds.")
                    sys.exit(0)


if __name__ == "__main__":
    shutdownSeconds = int(os.environ.get("SHUTDOWN_SECONDS", 10 * 60))
    scanChatList()
    sseChatList(shutdownSeconds)
