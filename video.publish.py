#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import json
import time
from pathlib import Path

import requests
from curl_cffi import requests as curl_req
from loguru import logger as log

from algo.w_rid import get_w_rid
from login import CookieDB


class VideoUploader:
    def __init__(self) -> None:
        self.db = CookieDB()

        self._init_session()

    def _init_session(self):
        self.session = curl_req.Session()
        self.session.cookies.update(self.db.get_cookie("19976752549"))
        self.session.headers.update(
            {
                "Accept": "*/*",
                "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Origin": "https://member.bilibili.com",
                "Pragma": "no-cache",
                "Referer": "https://member.bilibili.com/",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "cross-site",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
                "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
            }
        )
        self.session.verify = False
        self.session.timeout = 22

    @staticmethod
    def get_category(category: str):
        with open(
            Path(__file__).parent / "data/video.categories.json", "r", encoding="utf-8"
        ) as f:
            data = json.load(f)
            return [r for r in data if r["name"] == category][0]

    def preupload(self, filename: str, filesize: int):
        url = "https://member.bilibili.com/preupload"

        pre_resp = self.session.get(
            url,
            params={
                "probe_version": "20221109",
                "upcdn": "bldsa",
                "zone": "cs",
                "name": filename,
                "r": "upos",
                "profile": "ugcfx/bup",
                "ssl": "0",
                "version": "2.14.0.0",
                "build": "2140000",
                "size": str(filesize),
                "webVersion": "2.14.0",
            },
        )

        pre_resp_json = pre_resp.json()

        endpoint = pre_resp_json["endpoint"]
        upos_uri = pre_resp_json["upos_uri"].split("//")[-1]
        x_upos_auth = pre_resp_json["auth"]
        biz_id = pre_resp_json["biz_id"]

        log.info(
            f"PreUpload endpoint: {endpoint} upos_uri: {upos_uri}, biz_id: {biz_id}"
        )

        self.session.headers.update({"X-Upos-Auth": x_upos_auth})
        resp = self.session.post(
            f"https:{endpoint}/{upos_uri}",
            params={
                "uploads": "",
                "output": "json",
                "profile": "ugcfx/bup",
                "filesize": str(filesize),
                "partsize": "10485760",
                "biz_id": str(biz_id),
                "meta_upos_uri": f"{upos_uri.rsplit('.')[0]}.txt",
            },
        )
        resp_json = resp.json()

        log.info(f"PreUpload resp: {resp_json}")

        upload_id = resp_json["upload_id"]
        key = resp_json["key"]
        upos_uri = upos_uri.split("/")[0] + "/" + key
        return endpoint, upos_uri, upload_id, x_upos_auth, biz_id

    def upload(
        self,
        upload_id: str,
        endpoint: str,
        upos_uri: str,
        x_upos_auth: str,
        data: bytes,
        filesize: int,
    ):
        chunk_size = 10485760  # 10MB
        total_chunks = (filesize + chunk_size - 1) // chunk_size  # 计算总块数

        for chunk in range(1, total_chunks + 1):
            start = (chunk - 1) * chunk_size
            end = min(chunk * chunk_size, filesize)
            chunk_data = data[start:end]  # 获取当前分块的数据

            params = {
                "partNumber": str(chunk),
                "uploadId": upload_id,
                "chunk": str(chunk),
                "chunks": str(total_chunks),
                "size": str(len(chunk_data)),
                "start": str(start),
                "end": str(end),
                "total": str(filesize),
            }

            log.info(f"Uploading chunk {chunk}/{total_chunks}, params: {params}")

            try:
                resp = self.session.put(
                    f"https:{endpoint}/{upos_uri}", params=params, data=chunk_data
                )
                log.info(f"Upload chunk {chunk} response: {resp.text}")

                if resp.status_code != 200:
                    log.error(f"Upload failed for chunk {chunk}: {resp.text}")
                    return False

            except Exception as e:
                log.error(f"Error uploading chunk {chunk}: {e}")
                return False

        log.info("All chunks uploaded successfully")
        return True

    def merge_multipart(
        self, endpoint: str, upos_uri: str, filename: str, upload_id: str, biz_id: str
    ):
        params = {
            "output": "json",
            "name": filename,
            "profile": "ugcfx/bup",
            "uploadId": upload_id,
            "biz_id": biz_id,
        }
        data = {
            "parts": [
                {
                    "partNumber": 1,
                    "eTag": "etag",
                },
            ],
        }
        resp = self.session.post(
            f"https:{endpoint}/{upos_uri}", params=params, data=data
        )
        resp_json = resp.text
        log.info(f"Merge multipart resp: {resp_json}")

    def upload_img(self, img_path: str):
        params = {"wts": str(int(time.time()))}
        w_rid = get_w_rid(params)["w_rid"]
        params.update({"w_rid": w_rid})

        files = {
            "file_up": ("blob", open(img_path, "rb").read()),
            "biz": (None, "article"),
            "category": (None, "daily"),
            "csrf": (None, self.session.cookies.get("bili_jct")),
        }
        headers = {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9",
            "cache-control": "no-cache",
            "origin": "https://member.bilibili.com",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "referer": "https://member.bilibili.com/",
            "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        }

        resp = requests.post(
            "https://api.bilibili.com/x/dynamic/feed/draw/upload_bfs",
            params=params,
            files=files,
            headers=headers,
            cookies=self.session.cookies,
        )
        resp_json = resp.json()
        return [
            {
                "url": resp_json["data"]["image_url"],
                "width": resp_json["data"]["image_width"],
                "height": resp_json["data"]["image_height"],
                "size": resp_json["data"]["img_size"],
                "aigc": False,
            }
        ]

    def _publish(
        self,
        title: str,
        upos_uri: str,
        biz_id: str,
        cate_data: list,
        desc: str = None,
        cover: str = None,
        tag: str = None,
    ):
        params = {
            "web_location": "333.1024",
            "t": int(time.time() * 1000),
            "csrf": self.session.cookies.get("bili_jct"),
        }
        result = get_w_rid(params)
        params.update({"w_rid": result["w_rid"], "wts": result["wts"]})

        log.info(f"Publish params: {params}")

        data = {
            "videos": [
                {
                    "filename": upos_uri.split("/")[-1].split(".")[0],
                    "title": title,
                    "desc": "",
                    "cid": int(biz_id),
                },
            ],
            "cover": cover,
            "cover43": cover,
            "ai_cover": 0,
            "title": title,
            "copyright": 1,
            "human_type2": int(cate_data.get("id")),
            "tid": 21,
            "tag": tag,
            "desc": desc,
            "dynamic": "",
            "recreate": -1,
            "interactive": 0,
            "act_reserve_create": 0,
            "no_disturbance": 0,
            "is_only_self": 0,
            "watermark": {
                "state": 1,
            },
            "no_reprint": 1,
            "subtitle": {
                "open": 0,
                "lan": "",
            },
            "up_selection_reply": False,
            "up_close_reply": False,
            "up_close_danmu": False,
            "neutral_mark": "",
            "dolby": 0,
            "lossless_music": 0,
            "web_os": 1,
        }

        log.info(f"Publish data: {data}")
        resp = self.session.post(
            "https://member.bilibili.com/x/vu/web/add/v3",
            params=params,
            data=json.dumps(data, separators=(",", ":")),
        )
        resp_json = resp.text
        log.info(f"Publish resp: {resp_json}")

    def publish(
        self,
        title: str,
        category: str,
        video_path: str = None,
        desc: str = None,
        img_path: str = None,
        tag: str = None,
    ):
        cate_data = self.get_category(category)
        cover = self.upload_img(img_path)[0]["url"] if img_path else None
        path = Path(video_path)
        endpoint, upos_uri, upload_id, x_upos_auth, biz_id = self.preupload(
            path.name, path.stat().st_size
        )
        with open(path, "rb") as f:
            data = f.read()
            self.upload(
                upload_id, endpoint, upos_uri, x_upos_auth, data, path.stat().st_size
            )
        self.merge_multipart(endpoint, upos_uri, path.name, upload_id, biz_id)
        self._publish(title, upos_uri, biz_id, cate_data, desc, cover, tag)


if __name__ == "__main__":
    uploader = VideoUploader()

    uploader.publish(
        "AI 头脑风暴",
        video_path=r"c:/Users/xeliauk/Downloads/AI 头脑风暴.mp4",
        img_path=r"c:/Users/xeliauk/Downloads/生成大模型图.png",
        category="人工智能",
        tag="ai",
        desc="这是一个关于 AI 头脑风暴的视频",
    )
