"""
用於取得 Line 登入憑證的 script
會覆寫 ./secrets/line-credential.json
"""
import os
import sys
import json
import requests

lineCredentialPath = os.path.join("secrets", "line", "line-credential.json")
email = os.environ["LINE_ACCOUNT_EMAIL"]
password = os.environ["LINE_ACCOUNT_PASSWORD"]
defaultHeaders = {
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate",
    "accept-language": "en-US,en;q=0.9",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36",
}
session = requests.session()


def readJson(filename):
    if not os.path.exists(filename):
        writeJson(filename, {})
    with open(filename) as f:
        return json.load(f)


def writeJson(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4, sort_keys=True)


def getBots():
    return json.loads(
        session.get(
            url="https://chat.line.biz/api/v1/bots?noFilter=true&limit=1000",
            headers=defaultHeaders,
            data=None,
            allow_redirects=True,
        ).text
    )["list"]


def loginWithEmail():
    credential = readJson(lineCredentialPath)
    csrfToken = (
        session.get(
            url="https://account.line.biz/login?redirectUri=https%3A%2F%2Fchat.line.biz%2F",
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
                "Host": "account.line.biz",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36",
            },
            data=None,
            allow_redirects=True,
        )
        .text.split('name="x-csrf" content="')[1]
        .split('"')[0]
    )

    loginResult = session.post(
        url="https://account.line.biz/api/login/email",
        headers={
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Content-Type": "application/json;charset=UTF-8",
            "Host": "account.line.biz",
            "Origin": "https://account.line.biz",
            "Referer": "https://account.line.biz/login?redirectUri=https%3A%2F%2Fchat.line.biz%2F",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36",
            "X-XSRF-TOKEN": csrfToken,
        },
        json={"email": email, "password": password, "stayLoggedIn": False},
    )

    if loginResult.status_code != 200:
        sys.exit(f"Login Failed, Status Code: {loginResult.status_code}, Error: {loginResult.text}")

    accessToken = loginResult.headers["Set-Cookie"].split(";")[0].replace("ses=", "")

    credential["authToken"] = accessToken

    bots = getBots()
    if bots == []:
        sys.exit("[ ERROR ] No bot found on your account!!!")
    for n in range(len(bots)):
        print(str(n + 1) + ". " + bots[n]["name"])
    choice = int(input("Please Select Account: ")) - 1
    credential["mid"] = bots[choice]["botId"]
    credential["userId"] = bots[choice]["basicSearchId"]
    credential["name"] = bots[choice]["name"]

    writeJson(lineCredentialPath, credential)


if __name__ == "__main__":
    loginWithEmail()
