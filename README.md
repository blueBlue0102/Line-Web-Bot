# LINEOFFICIAL-WEBAPIBOT

透過 Line Web 介面的 API 進行操作，以達成一般 chatbot 做不到的功能  
例如更改對話者的暱稱或是狀態，目前 Line 官方的 API 並沒有提供這個功能

## Setup

先使用 pyenv 建立 3.11.1 的 python 環境

### 建立環境 & 安裝相依套件

```
pip install virtualenv
python -m virtualenv venv
```

切換至 venv 的環境後

```
pip install -r requirements.txt -r requirements-dev.txt
```

### 環境參數

`.example.env` 為環境參數的範例檔

- `LINE_ACCOUNT_EMAIL`  
  登入 Line 帳號用的 email
- `LINE_ACCOUNT_PASSWORD`  
  登入 Line 帳號用的 password
- `LINE_ACCOUNT_MID`  
  帳號的 id  
  可於 `https://chat.line.biz/{LINE_ACCOUNT_MID}` 取得

### 憑證

需要 firebase 的憑證  
目前憑證的位置固定放在專案根目錄的 `./secrets` 之下  

*註：由於 Cloud Run 無法 Mount 一個路徑下的多個檔案，所以各個憑證會再有自己的資料夾*

```
mkdir -p secrets/firebase
```

firebase 憑證須至 GCP firebase 中取得

## requirements.txt

`requirements.txt` 為運行本專案所必須的相依套件  
使用 `pipreqs` 進行更新 `requirements.txt`

```
pipreqs --encoding utf-8 --force
```

`requirements-dev.txt` 則為進行開發時才需要的套件

## Docker

### Build & Push Image

TODO: 改成正式專案的路徑

```
docker build . -t asia-east1-docker.pkg.dev/blue-chatbot-371911/hiking-bot/hiking-bot:1.0.0
docker push asia-east1-docker.pkg.dev/blue-chatbot-371911/hiking-bot/hiking-bot:1.0.0
```
