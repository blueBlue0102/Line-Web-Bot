import time
from datetime import datetime, timedelta
from firebaseClient import FirebaseClient
from function import Client


# Line Bot Init
client = Client()
# Firebase Init
firebaseClient = FirebaseClient()

# 抓取最多 25 個訊息未讀的訊息，判斷是否要建立行程
# 如果是，則開始建立行程的流程。建立完成後將訊息已讀
# 如果不是，則忽略
chatList = client.getChatList(folderType="UNREAD")["list"]
for chat in chatList:
    if chat["latestEvent"]["type"] == "message" and chat["latestEvent"]["message"]["type"] == "text":
        if chat["latestEvent"]["message"]["text"][0:5] == "#建立行程":
            tripId = chat["latestEvent"]["message"]["text"][6:]
            # 開始在 firebase 中進行尋找對應的行程
            tripData = firebaseClient.getTrip(tripId)
            if tripData is None:
                # 沒找到
                client.sendMessage(chat["chatId"], ("很抱歉，沒有找到對應的行程代碼\n" "請確認代碼沒有輸入錯誤，或是再試一次"))
                client.markAsRead(chat["chatId"], chat["latestEvent"]["message"]["id"])
                continue
            else:
                # 找到了，開始執行動作
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
                client.sendMessage(chat["chatId"], message)

                message = "已收到行程申請，提醒您，出發前回傳「登山當天的衣著」與「攜帶裝備之照片或清單」，才算完成申請程序，並於出發時回覆「啟動留守」後才會進行留守服務唷！"
                client.sendMessage(chat["chatId"], message)

                userName = client.getChat(chat["chatId"])["profile"]["name"]
                client.changeNickname(
                    chat["chatId"],
                    (
                        f"{userName[0: 2]}"
                        f"{inDatetime.month}/{inDatetime.day}-{outDatetime.day}"
                        f"{tripData['pathName'][0:2]}"
                        f"{outDatetime.hour}:{outDatetime.minute}"
                        f"+{tripData['delayHour']}"
                    ),
                )
                client.addFollowedUp(chat["chatId"])
                client.markAsRead(chat["chatId"], chat["latestEvent"]["message"]["id"])
        elif chat["latestEvent"]["message"]["text"][0:5] == "#結束行程":
            userName = client.getChat(chat["chatId"])["profile"]["name"]
            client.changeNickname(chat["chatId"], userName)
            client.sendMessage(chat["chatId"], "行程成功結束")
            client.addResolved(chat["chatId"])
            client.markAsRead(chat["chatId"], chat["latestEvent"]["message"]["id"])
    # 避免過於頻繁的呼叫 Line API
    # time.sleep(0.05)
print("done")
