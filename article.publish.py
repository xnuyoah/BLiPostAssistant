import json
import time
from pathlib import Path
from urllib.parse import urlencode

import requests
from curl_cffi import requests as curl_req
from loguru import logger as log

from algo.w_rid import get_w_rid
from login import CookieDB


class ArticleUploader:
    def __init__(self) -> None:
        self.db = CookieDB()

        self._init_session()

    def _init_session(self):
        self.session = curl_req.Session()
        self.session.cookies.update(self.db.get_cookie("19976752549"))
        self.session.headers.update(
            {
                "accept": "*/*",
                "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
                "cache-control": "no-cache",
                "content-type": "application/json",
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
        )
        self.session.verify = False
        self.session.timeout = 22

    @staticmethod
    def get_category_id(category: str):
        with open(
            Path(__file__).parent / "data/article.categories.json",
            "r",
            encoding="utf-8",
        ) as f:
            categories = json.load(f)
        for cat in categories:
            if cat["name"] == category:
                return cat["id"]
        return None

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

    def publish(self, title: str, content: str, category: str, img_path: str):
        category_id = self.get_category_id(category)
        cover = self.upload_img(img_path)
        data = {
            "raw_content": '{"ops":[{"insert":"%s\\n"}]}' % title,
            "opus_req": {
                "upload_id": "474253780_1758399725_518",
                "opus": {
                    "opus_source": 2,
                    "title": title,
                    "content": {
                        "paragraphs": [
                            {
                                "para_type": 1,
                                "text": {
                                    "nodes": [
                                        {
                                            "node_type": 1,
                                            "word": {
                                                "words": content,
                                                "font_size": 17,
                                                "font_level": "regular",
                                                "style": {},
                                            },
                                        },
                                    ],
                                },
                            },
                        ],
                    },
                    "article": {
                        "category_id": category_id,
                        "list_id": 0,
                        "originality": 0,
                        "reproduced": 0,
                        "cover": cover or None,
                        "biz_tags": [],
                    },
                    "pub_info": {},
                },
                "scene": 12,
                "meta": {
                    "app_meta": {
                        "from": "create.creative.web",
                        "mobi_app": "web",
                    },
                },
                "option": {
                    "aigc": 2,
                    "private_pub": 2,
                },
            },
        }
        params = {
            "csrf": self.session.cookies["bili_jct"],
            "gaia_source": "main_web",
            "dm_img_list": '[{"x":611,"y":-780,"z":0,"timestamp":228,"k":101,"type":0},{"x":739,"y":-823,"z":20,"timestamp":330,"k":114,"type":0},{"x":912,"y":-694,"z":164,"timestamp":443,"k":79,"type":0},{"x":863,"y":-861,"z":55,"timestamp":544,"k":65,"type":0},{"x":1057,"y":-1402,"z":16,"timestamp":645,"k":70,"type":0},{"x":1465,"y":-1227,"z":364,"timestamp":745,"k":123,"type":0},{"x":2853,"y":-4060,"z":86,"timestamp":2063,"k":69,"type":0},{"x":2998,"y":-3912,"z":222,"timestamp":2164,"k":97,"type":0},{"x":2197,"y":-298,"z":804,"timestamp":2687,"k":113,"type":0},{"x":1170,"y":-918,"z":97,"timestamp":2788,"k":86,"type":0},{"x":2030,"y":169,"z":943,"timestamp":2889,"k":83,"type":0},{"x":1652,"y":-107,"z":535,"timestamp":2990,"k":120,"type":0},{"x":1677,"y":-81,"z":557,"timestamp":3091,"k":104,"type":0},{"x":2568,"y":808,"z":1454,"timestamp":3455,"k":64,"type":0},{"x":1861,"y":-447,"z":1103,"timestamp":3559,"k":80,"type":0},{"x":1280,"y":-658,"z":677,"timestamp":4430,"k":117,"type":0},{"x":3012,"y":1559,"z":1667,"timestamp":4531,"k":120,"type":0},{"x":3155,"y":1828,"z":1639,"timestamp":4641,"k":97,"type":0},{"x":1812,"y":486,"z":293,"timestamp":5722,"k":78,"type":0},{"x":1940,"y":819,"z":427,"timestamp":5822,"k":119,"type":0},{"x":2266,"y":1463,"z":811,"timestamp":5922,"k":74,"type":0},{"x":2190,"y":1730,"z":833,"timestamp":6023,"k":72,"type":0},{"x":3772,"y":3425,"z":2444,"timestamp":6123,"k":103,"type":0},{"x":2522,"y":2204,"z":1199,"timestamp":6237,"k":89,"type":0},{"x":3735,"y":3424,"z":2414,"timestamp":6345,"k":61,"type":0},{"x":3440,"y":3129,"z":2119,"timestamp":6453,"k":91,"type":1},{"x":1341,"y":1023,"z":18,"timestamp":9647,"k":100,"type":0},{"x":4126,"y":3280,"z":2524,"timestamp":9748,"k":78,"type":0},{"x":2328,"y":1167,"z":521,"timestamp":9848,"k":119,"type":0},{"x":2467,"y":1294,"z":650,"timestamp":9955,"k":90,"type":0},{"x":4318,"y":3145,"z":2501,"timestamp":10120,"k":87,"type":1},{"x":2200,"y":1005,"z":380,"timestamp":13455,"k":111,"type":0},{"x":4570,"y":3098,"z":2776,"timestamp":13556,"k":100,"type":0},{"x":2934,"y":1398,"z":1171,"timestamp":13656,"k":66,"type":0},{"x":3133,"y":1586,"z":1380,"timestamp":13757,"k":118,"type":0},{"x":5356,"y":3983,"z":3679,"timestamp":13857,"k":75,"type":0},{"x":2141,"y":922,"z":554,"timestamp":13958,"k":119,"type":0},{"x":2495,"y":1403,"z":964,"timestamp":14059,"k":82,"type":0},{"x":2345,"y":1287,"z":827,"timestamp":14161,"k":86,"type":0},{"x":2558,"y":1500,"z":1040,"timestamp":14262,"k":63,"type":1},{"x":2127,"y":926,"z":440,"timestamp":14367,"k":108,"type":0},{"x":5505,"y":4190,"z":3608,"timestamp":14468,"k":84,"type":0},{"x":2767,"y":1464,"z":880,"timestamp":21271,"k":74,"type":0},{"x":5775,"y":4537,"z":3992,"timestamp":21370,"k":102,"type":0},{"x":6521,"y":5297,"z":4811,"timestamp":21471,"k":73,"type":0},{"x":5284,"y":4065,"z":3582,"timestamp":21574,"k":88,"type":0},{"x":3037,"y":1930,"z":1413,"timestamp":21676,"k":98,"type":0},{"x":3948,"y":2848,"z":2326,"timestamp":21782,"k":70,"type":0},{"x":5330,"y":4230,"z":3708,"timestamp":22044,"k":88,"type":1}]',
            "dm_img_str": "V2ViR0wgMS4wIChPcGVuR0wgRVMgMi4wIENocm9taXVtKQ",
            "dm_cover_img_str": "QU5HTEUgKE5WSURJQSwgTlZJRElBIEdlRm9yY2UgUlRYIDQwODAgU1VQRVIgKDB4MDAwMDI3MDIpIERpcmVjdDNEMTEgdnNfNV8wIHBzXzVfMCwgRDNEMTEpR29vZ2xlIEluYy4gKE5WSURJQS",
            "dm_img_inter": '{"ds":[{"t":7,"c":"YnJlLWJ0biBwcmltYXJ5IHNpemUtLWxhcm","p":[1083,31,491],"s":[282,765,928]}],"wh":[3426,4767,26],"of":[6792,9196,210]}',
            "w_opus_req.upload_id": "474253780_1758399725_518",
        }
        result = get_w_rid(params)
        w_rid, wts = result["w_rid"], result["wts"]
        params.update({"w_rid": w_rid, "wts": wts})

        log.info(f"Publish params: {params}")
        resp = self.session.post(
            f"https://api.bilibili.com/x/dynamic/feed/create/opus?{urlencode(params)}",
            data=json.dumps(data, separators=(",", ":")),
        )
        resp_json = resp.json()
        log.info(f"Publish resp: {resp_json}")


if __name__ == "__main__":
    video = ArticleUploader()
    video.publish(
        "测试标题", "测试内容", "游戏", r"C:\Users\xeliauk\Pictures\github.jpg"
    )
