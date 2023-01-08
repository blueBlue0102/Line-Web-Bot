# LINEOFFICIAL-WEBAPIBOT

透過 Line Web 介面的 API 進行操作，以達成一般 chatbot 做不到的功能  
例如更改對話者的暱稱或是狀態，目前 Line 官方的 API 並沒有提供這個功能

目前開發時的 python version = `3.7.15`  
之後須找方法統一專案的環境  
以及如何確保所有人環境中的套件版本都是一致的

## Setup

目前需要 Line 和 firebase 的憑證

Line 的憑證目前須經由手機掃描 QR code 登入來產生獲得  
可經由 `login.py` 來產生

firebase 憑證須至 GCP firebase 中取得
