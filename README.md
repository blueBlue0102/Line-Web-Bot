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

### 憑證

目前需要 Line 和 firebase 的憑證

```
mkdir -p secrets/line
mkdir -p secrets/firebase
```

#### Line

Line 的憑證目前須經由手機掃描 QR code 登入來產生獲得  
可經由 `login.py` 來產生

```
python login.py
```

#### Firebase

firebase 憑證須至 GCP firebase 中取得

## requirements.txt

使用 `pipreqs` 進行更新

```
pipreqs --encoding utf-8 --force
```

## Docker

### Build Image

```
docker build . -t linebot:1.0.0
```
