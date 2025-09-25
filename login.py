#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import base64
import json
import sqlite3
import time
from pathlib import Path
from urllib.parse import urlencode

from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
from Crypto.PublicKey import RSA
from curl_cffi import requests
from loguru import logger as log

from algo.geetest import Geetest

DB_NAME = str(Path(__file__).parent / "data/bilibili_users.db")


class CookieDB:
    def __init__(self, db_name=DB_NAME):
        self.conn = sqlite3.connect(db_name)
        self._create_table()

    def _create_table(self):
        sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            cookies TEXT,
            create_time INTEGER
        )
        """
        self.conn.execute(sql)
        self.conn.commit()

    def save(self, username: str, cookies: dict):
        sql = "INSERT INTO users (username, cookies, create_time) VALUES (?, ?, ?)"
        self.conn.execute(sql, (username, json.dumps(cookies), int(time.time())))
        self.conn.commit()
        log.info(f"✅ 用户 {username} cookies 已保存到数据库")

    def get_all(self):
        cursor = self.conn.execute(
            "SELECT id, username, cookies, create_time FROM users"
        )
        return cursor.fetchall()

    def get_cookie(self, username: str):
        sql = "SELECT cookies FROM users WHERE username = ?"
        cursor = self.conn.execute(sql, (username,))
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None

    def close(self):
        self.conn.close()


class Login:
    def __init__(self, username: str = "", password: str = ""):
        self.username = username
        self.password = password
        self._init_session()

    def _init_session(self):
        self.session = requests.Session()
        self.session.verify = False
        self.session.timeout = 22
        self.session.proxies = None

    def _get_captcha(self):
        resp = self.session.get(
            "https://passport.bilibili.com/x/passport-login/captcha",
            params={"source": "main-fe", "web_location": "333.1228"},
        )
        resp_json = resp.json()
        challenge = resp_json["data"]["geetest"]["challenge"]
        gt = resp_json["data"]["geetest"]["gt"]
        token = resp_json["data"]["token"]

        log.debug(f"get captcha, challenge: {challenge}, gt: {gt}, token: {token}")
        return challenge, gt, token

    def _encrypt_passwd(self):
        resp = self.session.get(
            "https://passport.bilibili.com/x/passport-login/web/key?_=1758400986904&web_location=333.1228"
        )
        resp_json = resp.json()
        key, _hash = resp_json["data"]["key"], resp_json["data"]["hash"]

        rsa_key = RSA.importKey(key)
        cipher = Cipher_pkcs1_v1_5.new(rsa_key)
        encrypted_password = base64.b64encode(
            cipher.encrypt((_hash + self.password).encode("utf-8"))
        ).decode("utf8")
        return encrypted_password

    def _login(self):
        challenge, gt, token = self._get_captcha()
        geetest = Geetest(gt=gt, challenge=challenge)
        validate = geetest.bypass()
        encrypted_password = self._encrypt_passwd()
        data = {
            "source": "main_web",
            "username": str(self.username),
            "password": encrypted_password,
            "go_url": "https://member.bilibili.com/",
            "token": token,
            "validate": validate,
            "seccode": f"{validate}|jordan",
            "challenge": challenge,
        }
        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://passport.bilibili.com",
            "referer": "https://passport.bilibili.com/login",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36",
        }

        resp = self.session.post(
            "https://passport.bilibili.com/x/passport-login/web/login",
            data=urlencode(data),
            headers=headers,
        )
        resp_json = resp.json()
        if (
            resp_json["data"]["message"]
            == "本次登录环境存在风险, 需使用手机号进行验证或绑定"
        ):
            url = resp_json["data"]["url"]
            captcha_key = self._send_sms_code(url)
            sms_code = input("请输入短信验证码: ")
            code = self._verify_sms_code(url, sms_code, captcha_key)
            cookies = self._get_cookies(code)
            return dict(cookies)
        else:
            return dict(self.session.cookies)

    def _get_web_ticket(self):
        resp = self.session.post(
            "https://api.bilibili.com/bapis/bilibili.api.ticket.v1.Ticket/GenWebTicket?key_id=ec02&hexsign=e3e63e2e6e41c8669f90227e731c76fc1888c115b4f30cf986cebce8e62db3f3&context[ts]=1758650544&csrf=",
        )
        resp_json = resp.json()
        return resp_json["data"]["ticket"]

    def _get_pre(self):
        resp = self.session.post(
            "https://passport.bilibili.com/x/safecenter/captcha/pre",
            data={"source": "risk"},
        )
        resp_json = resp.json()
        return (
            resp_json["data"]["recaptcha_token"],
            resp_json["data"]["gee_challenge"],
            resp_json["data"]["gee_gt"],
        )

    def _send_sms_code(self, url: str):
        token, challenge, gt = self._get_pre()
        geetest = Geetest(gt=gt, challenge=challenge)
        validate = geetest.bypass()
        ticket = self._get_web_ticket()
        data = {
            "tmp_code": url.rsplit("tmp_token=")[-1],
            "sms_type": "loginTelCheck",
            "recaptcha_token": token,
            "gee_challenge": challenge,
            "gee_seccode": f"{validate}|jordan",
            "gee_validate": validate,
        }
        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://passport.bilibili.com",
            "referer": f"https://passport.bilibili.com/pc/passport/riskVerify?{url.rsplit('?')[-1]}",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36",
        }

        self.session.headers.update(headers)
        self.session.cookies.update({"bili_ticket": ticket})
        resp = self.session.post(
            "https://passport.bilibili.com/x/safecenter/common/sms/send",
            data=urlencode(data),
        )
        return resp.json()["data"]["captcha_key"]

    def _verify_sms_code(self, url: str, sms_code: str, captcha_key: str):
        data = {
            "tmp_code": url.rsplit("tmp_token=")[-1],
            "captcha_key": captcha_key,
            "type": "loginTelCheck",
            "code": sms_code,
            "request_id": url.rsplit("&request_id=")[-1],
            "source": "risk",
        }
        resp = self.session.post(
            "https://passport.bilibili.com/x/safecenter/login/tel/verify",
            data=urlencode(data),
        )
        return resp.json()["data"]["code"]

    def _get_cookies(self, code: str):
        data = f"source=risk&code={code}&go_url=https:%2F%2Fmember.bilibili.com%2F"
        self.session.post(
            "https://passport.bilibili.com/x/passport-login/web/exchange_cookie",
            data=data,
        )
        return self.session.cookies

    def validate_cookies(self, cookies: dict):
        resp = requests.get(
            "https://api.bilibili.com/x/member/web/account?web_location=333.33",
            cookies=cookies,
        )
        resp_json = resp.json()
        return resp_json.get("message") != "请求错误"


if __name__ == "__main__":
    db = CookieDB()
    print(db.get_cookie("19976752549"))

    # mode = input("选择模式: 1=输入cookie, 2=账号密码登录 >>> ")

    # if mode == "1":
    #     raw = input("请输入cookies (key1=value1; key2=value2) >>> ")
    #     cookies = dict([kv.strip().split("=", 1) for kv in raw.split(";")])
    #     login = Login()
    #     if login.validate_cookies(cookies):
    #         username = input("请输入用户名备注 >>> ")
    #         db.save(username, cookies)
    #     else:
    #         log.error("❌ Cookie 无效，未保存")

    # elif mode == "2":
    #     username = ""
    #     password = ""
    #     login = Login(username, password)
    #     cookies = login._login()
    #     if login.validate_cookies(cookies):
    #         db.save(username, cookies)
    #     else:
    #         log.error("❌ 登录获取的 Cookie 无效")

    # log.info("数据库中已有用户：")
    # for row in db.get_all():
    #     log.info(row)

    # db.close()
