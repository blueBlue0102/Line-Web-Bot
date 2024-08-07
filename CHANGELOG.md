# CHANGELOG

## 1.2.2-recaptcha.0

- (hotfix) 提供寫死 cookie 登入的方式  
  新增兩個 env 參數，`LOGIN_WITH_COOKIE` 和 `COOKIE_SES`

## 1.2.2

- (fix) 更新 SSE loop 的程式邏輯，以避免無限死循環

## 1.2.1

- 修改 Dockerfile 中關於 Python 的啟動指令  
  增加 `-u` 的參數，讓 log 可以即時被印出來
  <https://stackoverflow.com/questions/29663459/python-app-does-not-print-anything-when-running-detached-in-docker>
- 更新 GCE 的位置，放到 hiking-guard 專案之下

## 1.2.0

- 重構程式碼，功能不變  
  將機器人邏輯獨立出另一個 class，而非放在 `run.py` 裡面
- 建立 Github Action CICD 流程，功能不變
- 更新 SSE 的 API version `v1` -> `v2`  
  `v1` 已被 LINE 棄用

## 1.1.1

- 拿掉下山時間的冒號字元

## 1.1.0

- 留守人傳送行程代碼時，也能觸發機器人建立行程的動作  
  留守人所傳遞的訊息必須只能包含行程代碼，例如 `T-1680872132224-XTW`，不能有任何多餘的文字
- 更改行程建立後，聊天室窗的命名規則  
  將會盡量的顯示行程名稱，而不總是只顯示前二個字

## 1.0.0

- 當管理員回覆【啟動留守】或【留守啟動】或貼圖  
  ![熊貼圖-啟動留守](https://stickershop.line-scdn.net/stickershop/v1/sticker/443245260/android/sticker.png)  
  機器人回傳「沿途有訊號時，記得回報人員狀況和座標位置喔。」
- 留守結束的判斷不限於【留守結束】，【結束留守】及貼圖也能觸發判斷  
  ![熊貼圖-留守結束](https://stickershop.line-scdn.net/stickershop/v1/sticker/443245261/android/sticker.png)