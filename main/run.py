import os
import re
import sys
import time
import json
import asyncio
from datetime import datetime, timedelta
from lineClient import LineClient
from firebaseClient import FirebaseClient

# TODO: 任何外部服務的叫用，都應設計失敗時的處理機制
# TODO: 要假設 Line 的 API 所回傳的 Data Type 可能改變


async def startTrip(chatId: str, tripId: str, username: str):
    """
    「建立行程」的處理邏輯
    """

    # 在 firebase 中進行尋找對應的行程
    tripData = firebaseClient.getTrip(tripId)
    if tripData is None:
        # 沒找到
        await lineClient.sendMessage(chatId, (f"很抱歉，沒有找到對應的行程代碼（{tripId}）\n" "請確認代碼沒有輸入錯誤，或是再試一次"))
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
    await lineClient.sendMessage(chatId, message)

    # 發送行程提醒
    message = "已收到行程申請，提醒您，出發前回傳「登山當天的衣著」與「攜帶裝備之照片或清單」，才算完成申請程序，並於出發時回覆「啟動留守」後才會進行留守服務唷！"
    await lineClient.sendMessage(chatId, message)

    # 更改暱稱
    await lineClient.changeNickname(
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
    await lineClient.addFollowedUp(chatId)

    # 釘選訊息
    await asyncio.sleep(1.5)
    messageEventList = await lineClient.getMessages(chatId)
    for messageEvent in messageEventList:
        if (
            messageEvent["type"] == "messageSent"
            and messageEvent["message"]["type"] == "text"
            and messageEvent["message"]["text"][0:20] == "【留守管理員通知頻道 - 旅程建立成功】"
        ):
            await lineClient.pinMessage(chatId, messageEvent["message"]["id"])
            break


async def stopTrip(chatId: str):
    """
    「結束行程」的處理邏輯
    """
    await lineClient.changeNickname(chatId, "")
    await lineClient.addResolved(chatId)
    pinnedMessageList = await lineClient.getPinnedMessage(chatId)
    for pinnedMessage in pinnedMessageList:
        if (
            pinnedMessage["type"] == "messageSent"
            and pinnedMessage["message"]["type"] == "text"
            and pinnedMessage["message"]["text"][0:20] == "【留守管理員通知頻道 - 旅程建立成功】"
        ):
            await lineClient.unpinMessage(chatId, pinnedMessage["message"]["id"])
            break


async def scanChatList():
    """
    抓取最多 25 個訊息 inbox 的訊息，判斷是否要建立行程
    如果是，則開始建立行程的流程
    如果不是，則忽略
    """

    def isClientSendingTextMsg(chat) -> bool:
        return chat["latestEvent"]["type"] == "message" and chat["latestEvent"]["message"]["type"] == "text"

    def isGuardSendingTextMsg(chat) -> bool:
        return chat["latestEvent"]["type"] == "messageSent" and chat["latestEvent"]["message"]["type"] == "text"

    def isTripStart(chat) -> bool:
        if chat["status"] == "blocked":
            return False
        msg = chat["latestEvent"]["message"]["text"]
        regResult = re.search("T-[0-9]{13}-[a-zA-Z0-9]{3}", msg)
        return regResult is not None

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
        return chat["status"] != "blocked" and chat["latestEvent"]["message"]["text"][0:4] == "留守結束"

    async def getUsername(chat) -> str:
        if chat["chatType"] == "USER":
            return chat["profile"]["name"]
        else:
            return (await lineClient.getChat(chat["chatId"]))["profile"]["name"]

    chatList = (await lineClient.getChatList(folderType="INBOX"))["list"]
    for chat in chatList:
        chatId = chat["chatId"]
        if isClientSendingTextMsg(chat):
            if isTripStart(chat):
                username = await getUsername(chat)
                tripId = getTripId(chat)
                await startTrip(chatId, tripId, username)
                print(f"User [{username}] start a trip.")
                await asyncio.sleep(0.25)
        elif isGuardSendingTextMsg(chat):
            if isTripStop(chat):
                username = await getUsername(chat)
                await stopTrip(chatId)
                print(f"User [{username}] stop a trip.")
                await asyncio.sleep(0.25)

    print(f"scanChatList Finish")


async def sseChatList(shutdownSeconds=10 * 60):
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

    def isGuardSendingTextMsg(chunk) -> bool:
        return (
            chunk["event"] == "chat"
            and "subEvent" in chunk
            and chunk["subEvent"] == "messageSent"
            and chunk["payload"]["message"]["type"] == "text"
        )

    def isTripStart(chunk) -> bool:
        msg = chunk["payload"]["message"]["text"]
        regResult = re.search("T-[0-9]{13}-[a-zA-Z0-9]{3}", msg)
        return regResult is not None

    def getTripId(chunk) -> str:
        msg = chunk["payload"]["message"]["text"]
        regResult = re.search("T-[0-9]{13}-[a-zA-Z0-9]{3}", msg)
        if regResult is None:
            return ""
        else:
            return regResult.group()

    def isTripStop(chunk) -> bool:
        return chunk["payload"]["message"]["text"][0:4] == "留守結束"

    def isTimesUp(startTime) -> bool:
        if shutdownSeconds <= 0:
            return False
        elif (time.time() - startTime) >= shutdownSeconds:
            return True
        else:
            return False

    poll = await lineClient.openPolling()
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
                            username = (await lineClient.getChat(chatId))["profile"]["name"]
                            await startTrip(chatId, tripId, username)
                            print(f"User [{username}] start a trip.")
                    elif isGuardSendingTextMsg(chunk):
                        chatId = chunk["payload"]["source"]["chatId"]
                        if isTripStop(chunk):
                            username = (await lineClient.getChat(chatId))["profile"]["name"]
                            await stopTrip(chatId)
                            print(f"User [{username}] stop a trip.")
                if isTimesUp(startTime):
                    print(f"Time's up: {shutdownSeconds} seconds.")
                    sys.exit(0)


async def main():
    await lineClient.loginWithEmail()
    shutdownSeconds = int(os.environ.get("SHUTDOWN_SECONDS", 10 * 60))
    await scanChatList()
    await sseChatList(shutdownSeconds)


if __name__ == "__main__":
    lineClient = LineClient()
    firebaseClient = FirebaseClient()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
