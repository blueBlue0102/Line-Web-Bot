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

`.example.env` 為環境參數的範例檔，內容包含各參數的說明

### 憑證

需要 firebase 的憑證  
目前憑證的位置固定放在專案根目錄的 `./secrets` 之下  

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

## 升版

當發布新版 bot 時，需進行以下行為：

- 更新 `.github/workflows/build-image-and-deploy-to-gce.yaml` 中的 `CHATBOT_VERSION`
- 更新 `CHANGELOG.md`
