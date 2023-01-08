# LINEOFFICIAL-WEBAPIBOT

透過 Line Web 介面的 API 進行操作，以達成一般 chatbot 做不到的功能  
例如更改對話者的暱稱或是狀態，目前 Line 官方的 API 並沒有提供這個功能

## Setup

```
pip install -r requirements.txt
```

### 憑證

目前需要 Line 和 firebase 的憑證

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
