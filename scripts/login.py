'''
用於取得 Line 登入憑證的 script
會覆寫 ./secrets/line-credential.json
'''
import os
import sys
import cv2
import json
import time
import numpy
import requests
import urllib.parse

lineCredentialPath = os.path.join('secrets', 'line-credential.json')
defaultHeaders = {
    'accept': 'application/json, text/plain, */*', 'accept-encoding': 'gzip, deflate',
    'accept-language': 'en-US,en;q=0.9', 'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36'}
session = requests.session()


def readJson(filename):
    if not os.path.exists(filename):
        writeJson(filename, {})
    with open(filename) as f:
        return json.load(f)


def writeJson(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4, sort_keys=True)


def displayQrCode(raw):
    img_array = numpy.asarray(bytearray(raw), dtype=numpy.uint8)
    img = cv2.imdecode(img_array, 0)
    cv2.imshow('QR code for login', img)
    cv2.waitKey(0)
    return

def getBots():
    return json.loads(session.get(
        url='https://chat.line.biz/api/v1/bots?noFilter=true&limit=1000',
        headers=defaultHeaders,
        data=None,
        allow_redirects=True
    ).text)["list"]

def loginWithQrCode():
    credential = readJson(lineCredentialPath)
    _csrf = session.get(
        url='https://account.line.biz/login?redirectUri=https%3A%2F%2Fchat.line.biz%2F',
        headers={
            'Accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'en-US,en;q=0.9', 'Connection': 'keep-alive',
            'Host': 'account.line.biz', 'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none', 'Sec-Fetch-User': '?1', 'Upgrade-Insecure-Requests': '1',
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36'},
        data=None, allow_redirects=True).text.split('name="x-csrf" content="')[1].split('"')[0]

    redir = session.post(
        url='https://account.line.biz/login/line?type=login',
        headers={
            'Accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'en-US,en;q=0.9', 'Cache-Control':
            'max-age=0', 'Connection': 'keep-alive', 'Host': 'account.line.biz',
            'Origin': 'https://account.line.biz',
            'Referer': 'https://account.line.biz/login?redirectUri=https%3A%2F%2Fchat.line.biz%2F',
            'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1', 'Upgrade-Insecure-Requests': '1',
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36'},
        data={"_csrf": _csrf},
        allow_redirects=False).headers["location"]

    auth_url = session.get(
        url=redir,
        headers={
            'accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,en;q=0.9', 'cache-control':
            'max-age=0', 'referer': 'https://account.line.biz/', 'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate', 'sec-fetch-site': 'cross-site', 'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36'},
        data=None, allow_redirects=False).headers["location"]

    _state = urllib.parse.unquote(auth_url).split('&state=')[1].split('&')[0]
    _loginState = urllib.parse.unquote(auth_url).split('loginState=')[1].split('&')[0]

    redir = session.get(
        url=auth_url,
        headers={
            'accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,en;q=0.9', 'cache-control':
            'max-age=0', 'cookie': 'loginState=N8ovqhoa5fRKNP9PbHIzWi', 'referer': 'https://account.line.biz/',
            'sec-fetch-dest': 'document', 'sec-fetch-mode': 'navigate', 'sec-fetch-site': 'cross-site',
            'sec-fetch-user': '?1', 'upgrade-insecure-requests': '1',
            'user-agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36'},
        data=None, allow_redirects=True).url

    qrCode = json.loads(
        session.get(
            url='https://access.line.me/qrlogin/v1/session?_=' + str(int(time.time())) + '&channelId=1576775644',
            headers={'accept': 'application/json, text/plain, */*', 'accept-encoding': 'gzip, deflate',
                     'accept-language': 'en-US,en;q=0.9', 'referer': redir, 'sec-fetch-dest': 'empty',
                     'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin',
                     'user-agent':
                     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36'},
            data=None, allow_redirects=True).text)["qrCodePath"]

    downloadData = session.get(
        url="https://access.line.me" + qrCode,
        headers={'accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8', 'accept-encoding': 'gzip, deflate',
                 'accept-language': 'en-US,en;q=0.9', 'referer': redir, 'sec-fetch-dest': 'image',
                 'sec-fetch-mode': 'no-cors', 'sec-fetch-site': 'same-origin',
                 'user-agent':
                 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36'},
        data=None, allow_redirects=True).content
    print("Please use cellphone to scan qrcode for login")
    print("PRESS ANY KEY BEFORE SCAN")
    print("PRESS ANY KEY BEFORE SCAN")
    print("PRESS ANY KEY BEFORE SCAN")
    displayQrCode(downloadData)
    print("Waiting for scan...")

    pinCode = json.loads(
        session.get(
            url='https://access.line.me/qrlogin/v1/qr/wait?_=' + str(int(time.time())) + '&channelId=1576775644',
            headers={'accept': 'application/json, text/plain, */*', 'accept-encoding': 'gzip, deflate',
                     'accept-language': 'en-US,en;q=0.9', 'referer': redir, 'sec-fetch-dest': 'empty',
                     'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin',
                     'user-agent':
                     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36'},
            data=None, allow_redirects=True).text)["pinCode"]
    print("Your pincode: "+pinCode)

    pinCodeCallback = session.get(
        url='https://access.line.me/qrlogin/v1/pin/wait?_=' + str(int(time.time())) + '&channelId=1576775644',
        headers={'accept': 'application/json, text/plain, */*', 'accept-encoding': 'gzip, deflate',
                 'accept-language': 'en-US,en;q=0.9', 'referer': redir, 'sec-fetch-dest': 'empty',
                 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin',
                 'user-agent':
                 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36'},
        data=None, allow_redirects=True)
    qrPinCert = pinCodeCallback.headers["set-cookie"].split('qrPinCert=')[1].split(";")[0]
    cert = pinCodeCallback.headers["set-cookie"].split('cert=')[1].split(";")[0]

    _csrf = session.cookies.get_dict()["X-SCGW-CSRF-Token"]
    authLogin = session.get(
        url='https://access.line.me/oauth2/v2.1/qr/authn?loginState=' + _loginState +
        '&loginChannelId=1576775644&returnUri=%2Foauth2%2Fv2.1%2Fauthorize%2Fconsent%3Fscope%3Dprofile%26response_type%3Dcode%26state%3D'
        + _state +
        '%26redirect_uri%3Dhttps%253A%252F%252Faccount.line.biz%252Flogin%252Fline-callback%26client_id%3D1576775644&__csrf='
        + _csrf,
        headers={
            'accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,en;q=0.9', 'referer': auth_url,
            'sec-fetch-dest': 'document', 'sec-fetch-mode': 'navigate', 'sec-fetch-site': 'same-origin',
            'upgrade-insecure-requests': '1',
            'user-agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36'},
        data=None, allow_redirects=False)
    authLogin_redir = session.get(
        url=authLogin.headers["location"],
        headers={
            'accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,en;q=0.9', 'referer': auth_url,
            'sec-fetch-dest': 'document', 'sec-fetch-mode': 'navigate', 'sec-fetch-site': 'same-origin',
            'upgrade-insecure-requests': '1',
            'user-agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36'},
        data=None, allow_redirects=False)
    authLogin_result = session.get(
        url=authLogin_redir.headers["location"],
        headers={
            'Accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'en-US,en;q=0.9', 'Connection': 'keep-alive',
            'Host': 'account.line.biz', 'Referer': 'https://access.line.me/', 'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'cross-site', 'Upgrade-Insecure-Requests': '1',
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36'},
        data=None, allow_redirects=False)
    credential["authToken"] = authLogin_result.headers["Set-Cookie"].split(";")[0].replace("ses=", "")

    bots = getBots()
    if bots == []:
        sys.exit("[ ERROR ] No bot found on your account!!!")
    for n in range(len(bots)):
        print(str(n+1)+'. '+bots[n]["name"])
    choice = int(input("Please Select Account: "))-1
    credential["mid"] = bots[choice]['botId']
    credential["userId"] = bots[choice]['basicSearchId']
    credential["name"] = bots[choice]['name']

    writeJson(lineCredentialPath, credential)




loginWithQrCode()
