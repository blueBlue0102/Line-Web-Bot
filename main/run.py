import time
import json
import traceback
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
        lineClient.sendMessage(chatId, ("很抱歉，沒有找到對應的行程代碼\n" "請確認代碼沒有輸入錯誤，或是再試一次"))
        return

    # 找到了，開始執行動作
    # 發送行程資訊
    inDatetime = datetime.strptime(tripData["inDatetime"], "%Y-%m-%dT%H:%M:%S.%fZ") + timedelta(hours=8)
    outDatetime = datetime.strptime(tripData["outDatetime"], "%Y-%m-%dT%H:%M:%S.%fZ") + timedelta(hours=8)
    message = (
        f"【留守管理員通知頻道】\n"
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


def stopTrip(chatId: str):
    """
    「結束行程」的處理邏輯
    """
    lineClient.changeNickname(chatId, "")
    lineClient.sendMessage(chatId, "行程成功結束")
    lineClient.addResolved(chatId)


def scanChatList():
    """
    抓取最多 25 個訊息 inbox 的訊息，判斷是否要建立行程
    如果是，則開始建立行程的流程
    如果不是，則忽略
    """

    def isTripStart(chat) -> bool:
        return chat["status"] != "blocked" and chat["latestEvent"]["message"]["text"][0:5] == "#建立行程"

    def getTripId(chat) -> str:
        return chat["latestEvent"]["message"]["text"][6:]

    def isTripStop(chat) -> bool:
        return chat["status"] != "blocked" and chat["latestEvent"]["message"]["text"][0:5] == "#結束行程"

    def getUsername(chat) -> str:
        if chat["chatType"] == "USER":
            return chat["profile"]["name"]
        else:
            return lineClient.getChat(chat["chatId"])["profile"]["name"]

    count = 0
    chatList = lineClient.getChatList(folderType="INBOX")["list"]
    for chat in chatList:
        if chat["latestEvent"]["type"] == "message" and chat["latestEvent"]["message"]["type"] == "text":
            trigger = True
            count += 1
            chatId = chat["chatId"]
            if isTripStart(chat):
                username = getUsername(chat)
                tripId = getTripId(chat)
                startTrip(chatId, tripId, username)
                print(f"scanChatList: User [{username}] start a trip.")
            elif isTripStop(chat):
                stopTrip(chatId)
                print(f"scanChatList: User [{username}] stop a trip.")
            else:
                trigger = False
                count -= 1

            # 避免過於頻繁的呼叫 Line API
            if trigger:
                time.sleep(0.25)

    print(f"scanChatList Finish: {count}")


def sseChatList():
    """
    透過 SSE 取得 Line 的即時訊息通知
    收到訊息後，依據內容執行不同行為
    """

    def isTripStart(chunk) -> bool:
        return chunk["payload"]["message"]["text"][0:5] == "#建立行程"

    def getTripId(chunk) -> str:
        return chunk["payload"]["message"]["text"][6:]

    def isTripStop(chunk) -> bool:
        return chunk["payload"]["message"]["text"][0:5] == "#結束行程"

    poll = lineClient.openPolling()
    with poll.getresponse() as response:
        while not response.closed:
            for data in response:
                decodedData = data.decode("utf-8")
                if "data:{" in decodedData:
                    chunk = json.loads(decodedData.replace("data:", ""))
                    if (
                        chunk["event"] == "chat"
                        and "subEvent" in chunk
                        and chunk["subEvent"] == "message"
                        and chunk["payload"]["message"]["type"] == "text"
                    ):
                        chatId = chunk["payload"]["source"]["chatId"]
                        if isTripStart(chunk):
                            tripId = getTripId(chunk)
                            username = lineClient.getChat(chatId)["profile"]["name"]
                            startTrip(chatId, tripId, username)
                            print(f"sseChatList: User [{username}] start a trip.")
                        elif isTripStop(chunk):
                            stopTrip(chatId)
                            print(f"sseChatList: User [{username}] stop a trip.")


if __name__ == "__main__":
    errorRetry = 0
    count = 0
    while True:
        try:
            count += 1
            print(f"Start: {count}")
            scanChatList()
            sseChatList()
        except Exception as e:
            if errorRetry >= 3:
                raise (e)
            else:
                traceback.print_exc()
                errorRetry += 1
                print(f"Error Retry: {errorRetry}")
