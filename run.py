from datetime import datetime
from function import *

client = Client()
if True:
    poll = client.openPolling()
    with poll.getresponse() as response:
        while not response.closed:
            for chunk in response:
                if "data:{" in chunk.decode('utf-8'):
                    chunk = json.loads(chunk.decode('utf-8').replace("data:", ""))
                    # print(chunk)
                    event = chunk["event"]
                    if event == "chat" and "subEvent" in chunk and chunk["subEvent"] == "message":
                        msg = chunk["payload"]["message"]
                        chatId = chunk["payload"]["source"]["chatId"]
                        if msg["type"] == "text":
                            text = msg["text"]
                            cmd = text.lower()
                            # print('chatId:', chatId, '\nmsg:', cmd)
                            if cmd == "hello":
                                client.getChat(chatId)
                                client.sendMessage(chatId, "hai")
                            elif cmd == "#建立行程":
                                userName = client.getChat(chatId)['profile']['name']
                                client.changeNickname(chatId, userName[0:2]+datetime.now().strftime("%H:%M:%S"))
                                client.addFollowedUp(chatId)
                                client.sendMessage(chatId, "行程成功建立")
                            elif cmd == "#結束行程":
                                userName = client.getChat(chatId)['profile']['name']
                                client.changeNickname(chatId, userName)
                                client.sendMessage(chatId, "行程成功結束")
                                client.addResolved(chatId)

                    elif event == "chat" and "subEvent" in chunk and chunk["subEvent"] == "chatRead":
                        chatId = chunk["payload"]["source"]["chatId"]
                        # READ DETECTION

                    # else:
                    #     print(chunk)

# if True:
#     print(client.get)
