#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import hashlib
import json
import math
import random
import time
from pathlib import Path

import cv2
import numpy as np
import onnxruntime
from cryptography.hazmat.primitives import padding, serialization
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from curl_cffi import requests as curl_requests
from fake_useragent import UserAgent
from loguru import logger as log

MODEL_DIR = Path(__file__).parent / "models"
YOLO_ONNX_PATH = MODEL_DIR / "yolo.onnx"
SIAMESE_ONNX_PATH = MODEL_DIR / "siamese.onnx"
DETECT_CLASSES = ["big", "small"]
PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDB45NNFhRGWzMFPn9I7k7IexS5
XviJR3E9Je7L/350x5d9AtwdlFH3ndXRwQwprLaptNb7fQoCebZxnhdyVl8Jr2J3
FZGSIa75GJnK4IwNaG10iyCjYDviMYymvCtZcGWSqSGdC/Bcn2UCOiHSMwgHJSrg
Bm1Zzu+l8nSOqAurgQIDAQAB
-----END PUBLIC KEY-----"""

MOUSE_TRACK = [
    ["move", 150, 300, 1758624000100, "pointermove"],
    ["move", 152, 300, 1758624000120, "pointermove"],
    ["move", 155, 301, 1758624000150, "pointermove"],
    ["move", 159, 301, 1758624000180, "pointermove"],
    ["move", 164, 302, 1758624000210, "pointermove"],
    ["move", 170, 302, 1758624000240, "pointermove"],
    ["move", 176, 303, 1758624000270, "pointermove"],
    ["move", 182, 303, 1758624000300, "pointermove"],
    ["move", 188, 304, 1758624000330, "pointermove"],
    ["move", 195, 304, 1758624000360, "pointermove"],
    ["move", 202, 305, 1758624000390, "pointermove"],
    ["move", 208, 305, 1758624000420, "pointermove"],
    ["move", 215, 306, 1758624000450, "pointermove"],
    ["move", 222, 306, 1758624000480, "pointermove"],
    ["move", 228, 307, 1758624000510, "pointermove"],
    ["move", 235, 307, 1758624000540, "pointermove"],
    ["move", 241, 308, 1758624000570, "pointermove"],
    ["move", 247, 308, 1758624000600, "pointermove"],
    ["move", 253, 309, 1758624000630, "pointermove"],
    ["move", 258, 309, 1758624000660, "pointermove"],
    ["move", 263, 310, 1758624000690, "pointermove"],
    ["move", 267, 310, 1758624000720, "pointermove"],
    ["move", 271, 311, 1758624000750, "pointermove"],
    ["move", 275, 311, 1758624000780, "pointermove"],
    ["move", 278, 312, 1758624000810, "pointermove"],
    ["move", 281, 312, 1758624000840, "pointermove"],
    ["move", 283, 313, 1758624000870, "pointermove"],
    ["move", 285, 313, 1758624000900, "pointermove"],
    ["move", 286, 314, 1758624000930, "pointermove"],
    ["move", 287, 314, 1758624000960, "mousemove"],
    ["move", 288, 315, 1758624000990, "pointermove"],
    ["move", 289, 315, 1758624001020, "pointermove"],
    ["down", 289, 315, 1758624001200, "pointerdown"],
    ["up", 289, 315, 1758624001250, "pointerup"],
    ["move", 292, 316, 1758624001320, "pointermove"],
    ["move", 296, 317, 1758624001380, "pointermove"],
    ["move", 301, 318, 1758624001440, "pointermove"],
    ["move", 306, 319, 1758624001500, "pointermove"],
    ["move", 312, 320, 1758624001560, "pointermove"],
    ["move", 318, 321, 1758624001620, "pointermove"],
    ["move", 324, 322, 1758624001680, "pointermove"],
    ["move", 330, 323, 1758624001740, "pointermove"],
    ["move", 336, 324, 1758624001800, "pointermove"],
    ["move", 342, 325, 1758624001860, "pointermove"],
    ["move", 347, 326, 1758624001920, "pointermove"],
    ["move", 352, 327, 1758624001980, "pointermove"],
    ["move", 356, 328, 1758624002040, "pointermove"],
    ["move", 360, 329, 1758624002100, "pointermove"],
    ["move", 363, 330, 1758624002160, "pointermove"],
    ["move", 366, 331, 1758624002220, "pointermove"],
    ["move", 368, 332, 1758624002280, "pointermove"],
    ["move", 370, 333, 1758624002340, "pointermove"],
    ["move", 371, 334, 1758624002400, "mousemove"],
    ["down", 371, 334, 1758624002550, "pointerdown"],
    ["up", 371, 334, 1758624002610, "pointerup"],
    ["move", 370, 336, 1758624002680, "pointermove"],
    ["move", 368, 338, 1758624002750, "pointermove"],
    ["move", 365, 340, 1758624002820, "pointermove"],
    ["move", 362, 342, 1758624002890, "pointermove"],
    ["move", 358, 344, 1758624002960, "pointermove"],
    ["move", 353, 346, 1758624003030, "pointermove"],
    ["move", 348, 348, 1758624003100, "pointermove"],
    ["move", 342, 350, 1758624003170, "pointermove"],
    ["move", 336, 352, 1758624003240, "pointermove"],
    ["move", 329, 354, 1758624003310, "pointermove"],
    ["move", 322, 356, 1758624003380, "pointermove"],
    ["move", 315, 358, 1758624003450, "pointermove"],
    ["move", 308, 360, 1758624003520, "pointermove"],
    ["move", 301, 362, 1758624003590, "pointermove"],
    ["move", 294, 364, 1758624003660, "pointermove"],
    ["move", 287, 366, 1758624003730, "pointermove"],
    ["move", 280, 368, 1758624003800, "pointermove"],
    ["move", 273, 370, 1758624003870, "pointermove"],
    ["move", 266, 372, 1758624003940, "pointermove"],
    ["move", 259, 374, 1758624004010, "mousemove"],
    ["down", 259, 374, 1758624004180, "pointerdown"],
    ["up", 259, 374, 1758624004240, "pointerup"],
    ["move", 265, 372, 1758624004310, "pointermove"],
    ["move", 272, 370, 1758624004380, "pointermove"],
    ["move", 279, 368, 1758624004450, "pointermove"],
    ["move", 286, 366, 1758624004520, "pointermove"],
    ["move", 293, 364, 1758624004590, "pointermove"],
    ["move", 300, 362, 1758624004660, "pointermove"],
    ["move", 307, 360, 1758624004730, "pointermove"],
    ["move", 314, 358, 1758624004800, "pointermove"],
    ["move", 321, 356, 1758624004870, "pointermove"],
    ["move", 328, 354, 1758624004940, "pointermove"],
    ["move", 335, 352, 1758624005010, "pointermove"],
    ["move", 341, 350, 1758624005080, "pointermove"],
    ["move", 347, 348, 1758624005150, "pointermove"],
    ["move", 352, 346, 1758624005220, "pointermove"],
    ["move", 357, 344, 1758624005290, "pointermove"],
    ["move", 361, 342, 1758624005360, "pointermove"],
    ["move", 364, 340, 1758624005430, "pointermove"],
    ["move", 367, 338, 1758624005500, "pointermove"],
    ["move", 369, 336, 1758624005570, "pointermove"],
    ["move", 370, 334, 1758624005640, "mousemove"],
    ["down", 370, 334, 1758624005810, "pointerdown"],
    ["focus", 1758624005810],
    ["up", 370, 334, 1758624005870, "pointerup"],
]


def _retry(max_retries=3, delay=1, exceptions=(Exception,)):
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_err = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_err = e
                    log.warning(
                        f"{func.__name__} 请求失败({attempt}/{max_retries}): {e}"
                    )
                    if attempt < max_retries:
                        time.sleep(delay * attempt)
            log.error(f"{func.__name__} 重试 {max_retries} 次后仍然失败")
            raise last_err

        return wrapper

    return decorator


class Detector:
    def __init__(self):
        if not YOLO_ONNX_PATH.exists():
            raise FileNotFoundError(f"YOLO 模型文件不存在: {YOLO_ONNX_PATH}")
        if not SIAMESE_ONNX_PATH.exists():
            raise FileNotFoundError(f"Siamese 模型文件不存在: {SIAMESE_ONNX_PATH}")
        self.img = None
        self.yolo_session = onnxruntime.InferenceSession(str(YOLO_ONNX_PATH))
        self.siamese_session = onnxruntime.InferenceSession(str(SIAMESE_ONNX_PATH))
        self.classes = DETECT_CLASSES
        self.color_palette = np.random.uniform(0, 255, size=(len(self.classes), 3))

    @staticmethod
    def _preprocess_img(img: np.ndarray, size: tuple = (105, 105)) -> np.ndarray:
        img_resized = cv2.resize(img, size)
        img_normalized = np.array(img_resized) / 255.0
        img_transposed = np.transpose(img_normalized, (2, 0, 1))
        img_expanded = np.expand_dims(img_transposed, axis=0).astype(np.float32)
        return img_expanded

    def siamese(
        self, small_imgs: dict, bg_img_boxes: list, show_result: bool = False
    ) -> list:
        try:
            small_imgs_preprocessed = {
                idx: self._preprocess_img(small_imgs[idx]) for idx in sorted(small_imgs)
            }

            results = []

            for idx in sorted(small_imgs_preprocessed):
                img_content1 = small_imgs_preprocessed[idx]

                for box in bg_img_boxes:
                    if [box[0], box[1]] in results:
                        continue

                    cropped_img = self.img[
                        box[1] : box[1] + box[3], box[0] : box[0] + box[2]
                    ]

                    img_content2 = self._preprocess_img(cropped_img)

                    input_data = {"input": img_content1, "input.53": img_content2}
                    output = self.siamese_session.run(None, input_data)

                    output_sigmoid = 1 / (1 + np.exp(-output[0]))
                    ret = output_sigmoid[0][0]

                    if ret >= 0.1:
                        results.append([box[0], box[1]])
                        break

            for i in results:
                cv2.circle(self.img, (i[0] + 30, i[1] + 30), 5, (0, 0, 255), 5)

            if show_result:
                cv2.imwrite("result.jpg", self.img)

            return results
        except Exception as e:
            log.error(f"Siamese 匹配失败: {e}")
            raise

    def detect(self, img: bytes) -> tuple[dict, list]:
        try:
            confidence_threshold = 0.8
            iou_threshold = 0.8

            model_inputs = self.yolo_session.get_inputs()
            model_input_shape = model_inputs[0].shape
            model_input_width = model_input_shape[2]
            model_input_height = model_input_shape[3]

            self.img = cv2.imdecode(np.frombuffer(img, np.uint8), cv2.IMREAD_ANYCOLOR)
            if self.img is None:
                raise ValueError("无法解码图像数据")

            img_height, img_width = self.img.shape[:2]
            img_rgb = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)
            img_resized = cv2.resize(img_rgb, (model_input_width, model_input_height))

            img_data = np.array(img_resized) / 255.0
            img_data = np.transpose(img_data, (2, 0, 1))
            img_data = np.expand_dims(img_data, axis=0).astype(np.float32)

            inputs = {model_inputs[0].name: img_data}
            outputs = self.yolo_session.run(None, inputs)
            outputs = np.transpose(np.squeeze(outputs[0]))

            rows = outputs.shape[0]
            boxes, scores, class_ids = [], [], []
            x_factor = img_width / model_input_width
            y_factor = img_height / model_input_height

            for i in range(rows):
                classes_scores = outputs[i][4:]
                max_score = np.amax(classes_scores)
                if max_score >= confidence_threshold:
                    class_id = np.argmax(classes_scores)
                    x, y, w, h = (
                        outputs[i][0],
                        outputs[i][1],
                        outputs[i][2],
                        outputs[i][3],
                    )
                    left = int((x - w / 2) * x_factor)
                    top = int((y - h / 2) * y_factor)
                    width = int(w * x_factor)
                    height = int(h * y_factor)
                    class_ids.append(class_id)
                    scores.append(max_score)
                    boxes.append([left, top, width, height])

            indices = cv2.dnn.NMSBoxes(
                boxes, scores, confidence_threshold, iou_threshold
            )
            new_boxes = [boxes[i] for i in indices]
            small_imgs, big_img_boxes = {}, []
            for box in new_boxes:
                cropped = self.img[box[1] : box[1] + box[3], box[0] : box[0] + box[2]]
                if cropped.shape[0] < 35 and cropped.shape[1] < 35:
                    small_imgs[box[0]] = cropped
                else:
                    big_img_boxes.append(box)
            return small_imgs, big_img_boxes
        except Exception as e:
            log.error(f"YOLO 检测失败: {e}")
            raise


class Bypass:
    def __init__(self, gt: str = None, challenge: str = None) -> None:
        self.gt = gt
        self.challenge = challenge
        self.pic_path = None
        self.s = None
        self.c = None
        self.aes_key = "".join(
            f"{int((1 + random.random()) * 65536):04x}"[1:] for _ in range(4)
        )
        self.public_key = serialization.load_pem_public_key(PUBLIC_KEY.encode())
        self.encrypt_key = self.public_key.encrypt(
            self.aes_key.encode(), PKCS1v15()
        ).hex()
        self.mouse_track = MOUSE_TRACK
        self._init_session()

    def _init_session(self):
        self.session = curl_requests.Session()
        self.session.headers = {"User-Agent": UserAgent().random}
        self.session.verify = False
        self.session.proxy = None
        self.session.timeout = 22

    @staticmethod
    def md5(text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()

    def aes_encrypt(self, text: str) -> bytes:
        cipher = Cipher(
            algorithms.AES(self.aes_key.encode()), modes.CBC(b"0000000000000000")
        )
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(128).padder()
        padded_content = padder.update(text.encode()) + padder.finalize()
        return encryptor.update(padded_content) + encryptor.finalize()

    @staticmethod
    def encode_mouse_path(path: list, c: list, s: str) -> str:
        def preprocess(path: list) -> list:
            def BFIQ(e):
                t = 32767
                if not isinstance(e, int):
                    return e
                else:
                    if t < e:
                        e = t
                    elif e < -t:
                        e = -t
                return round(e)

            def BGAB(e):
                t = ""
                n = 0
                while n < len(e) and not t:
                    if e[n]:
                        t = e[n][4]
                    n += 1
                if not t:
                    return e
                r = ""
                i = ["mouse", "touch", "pointer", "MSPointer"]
                for s in range(len(i)):
                    if t.startswith(i[s]):
                        r = i[s]
                _ = list(e)
                for a in range(len(_) - 1, -1, -1):
                    c = _[a]
                    l = c[0]
                    if l in ["move", "down", "up"]:
                        value = c[4] or ""
                        if not value.startswith(r):
                            _.pop(a)
                return _

            t = 0
            n = 0
            r = []
            s = 0
            if len(path) <= 0:
                return []
            o = None
            _ = None
            a = BGAB(path)
            c_len = len(a)
            for l in range(0 if c_len < 300 else c_len - 300, c_len):
                u = a[l]
                h = u[0]
                if h in ["down", "move", "up", "scroll"]:
                    if not o:
                        o = u
                    _ = u
                    r.append([h, [u[1] - t, u[2] - n], BFIQ(u[3] - s if s else s)])
                    t = u[1]
                    n = u[2]
                    s = u[3]
                elif h in ["blur", "focus", "unload"]:
                    r.append([h, BFIQ(u[1] - s if s else s)])
                    s = u[1]
            return r

        def process(prepared_path: list) -> str:
            h = {
                "move": 0,
                "down": 1,
                "up": 2,
                "scroll": 3,
                "focus": 4,
                "blur": 5,
                "unload": 6,
                "unknown": 7,
            }

            def p(e, t):
                n = bin(e)[2:]
                r = ""
                i = len(n) + 1
                while i <= t:
                    i += 1
                    r += "0"
                return r + n

            def d(e):
                t = []
                n = len(e)
                r = 0
                while r < n:
                    i = e[r]
                    s = 0
                    while True:
                        if s >= 16:
                            break
                        o = r + s + 1
                        if o >= n:
                            break
                        if e[o] != i:
                            break
                        s += 1
                    r += 1 + s
                    _ = h[i]
                    if s != 0:
                        t.append(_ | 8)
                        t.append(s - 1)
                    else:
                        t.append(_)
                a = p(n | 32768, 16)
                c = ""
                for l in range(len(t)):
                    c += p(t[l], 4)
                return a + c

            def g(e, tt):
                def temp1(e1):
                    n = len(e)
                    r = 0
                    i = []
                    while r < n:
                        s = 1
                        o = e[r]
                        _ = abs(o)
                        while True:
                            if n <= r + s:
                                break
                            if e[r + s] != o:
                                break
                            if (_ >= 127) or (s >= 127):
                                break
                            s += 1
                        if s > 1:
                            i.append((49152 if o < 0 else 32768) | s << 7 | _)
                        else:
                            i.append(o)
                        r += s
                    return i

                e = temp1(e)

                r = []
                i = []

                def n(e, t):
                    return 0 if e == 0 else math.log(e) / math.log(t)

                for temp in e:
                    t = math.ceil(n(abs(temp) + 1, 16))
                    if t == 0:
                        t = 1
                    r.append(p(t - 1, 2))
                    i.append(p(abs(temp), t * 4))

                s = "".join(r)
                o = "".join(i)

                def temp2(t):
                    return t != 0 and t >> 15 != 1

                def temp3(e1):
                    n = []

                    def temp(e2):
                        if temp2(e2):
                            n.append(e2)

                    for r in range(len(e1)):
                        temp(e1[r])
                    return n

                def temp4(t):
                    if t < 0:
                        return "1"
                    else:
                        return "0"

                if tt:
                    n = []
                    e1 = temp3(e)
                    for r in range(len(e1)):
                        n.append(temp4(e1[r]))
                    n = "".join(n)
                else:
                    n = ""
                return p(len(e) | 32768, 16) + s + o + n

            def u(e):
                t = ""
                n = len(e) // 6
                for r in range(n):
                    t += "()*,-./0123456789:?@ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz~"[
                        int(e[6 * r : 6 * (r + 1)], 2)
                    ]
                return t

            t = []
            n = []
            r = []
            i = []
            for a in range(len(prepared_path)):
                _ = prepared_path[a]
                a_len = len(_)
                t.append(_[0])
                n.append(_[1] if a_len == 2 else _[2])
                if a_len == 3:
                    r.append(_[1][0])
                    i.append(_[1][1])
            c_str = d(t) + g(n, False) + g(r, True) + g(i, True)
            l = len(c_str)
            if l % 6 != 0:
                c_str += p(0, 6 - l % 6)
            return u(c_str)

        def postprocess(e: str, t: list, n: str) -> str:
            i = 0
            s = e
            o = t[0]
            _ = t[2]
            a = t[4]
            while True:
                r = n[i : i + 2]
                if not r:
                    break
                i += 2
                c = int(r, 16)
                l = chr(c)
                u = (o * c * c + _ * c + a) % len(s)
                s = s[:u] + l + s[u:]
            return s

        return postprocess(process(preprocess(path)), c, s)

    @staticmethod
    def encode(input_bytes: list) -> str:
        def get_char_from_index(index: int) -> str:
            char_table = (
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789()"
            )
            return char_table[index] if 0 <= index < len(char_table) else "."

        def transform_value(value: int, bit_mask: int) -> int:
            result = 0
            for r in range(23, -1, -1):
                if (bit_mask >> r) & 1:
                    result = (result << 1) + ((value >> r) & 1)
            return result

        encoded_string = ""
        padding = ""
        input_length = len(input_bytes)
        for i in range(0, input_length, 3):
            chunk_length = min(3, input_length - i)
            chunk = input_bytes[i : i + chunk_length]
            if chunk_length == 3:
                value = (chunk[0] << 16) + (chunk[1] << 8) + chunk[2]
                encoded_string += (
                    get_char_from_index(transform_value(value, 7274496))
                    + get_char_from_index(transform_value(value, 9483264))
                    + get_char_from_index(transform_value(value, 19220))
                    + get_char_from_index(transform_value(value, 235))
                )
            elif chunk_length == 2:
                value = (chunk[0] << 16) + (chunk[1] << 8)
                encoded_string += (
                    get_char_from_index(transform_value(value, 7274496))
                    + get_char_from_index(transform_value(value, 9483264))
                    + get_char_from_index(transform_value(value, 19220))
                )
                padding = "."
            elif chunk_length == 1:
                value = chunk[0] << 16
                encoded_string += get_char_from_index(
                    transform_value(value, 7274496)
                ) + get_char_from_index(transform_value(value, 9483264))
                padding = ".."
        return encoded_string + padding

    @_retry()
    def _get_type(self) -> dict:
        try:
            url = f"https://api.geetest.com/gettype.php?gt={self.gt}"
            res = self.session.get(url, timeout=10)
            res.raise_for_status()
            return json.loads(res.text[1:-1])["data"]
        except (curl_requests.exceptions.RequestException, ValueError) as e:
            log.error(f"获取类型失败: {e}")
            raise

    @_retry()
    def _ajax(self) -> dict:
        try:

            def transform(e: str, t: list, n: str) -> str:
                if not t or not n:
                    return e
                o = 0
                i = list(e)
                s = t[0]
                a = t[2]
                b = t[4]
                while o < len(n):
                    r = n[o : o + 2]
                    o += 2
                    c = int(r, 16)
                    l = chr(c)
                    u = (s * c * c + a * c + b) % len(i)
                    i.insert(u, l)
                return "".join(i)

            transformed_mouse_track = transform(
                self.encode_mouse_path(self.mouse_track, self.c, self.s), self.c, self.s
            )

            rp = self.md5(self.gt + self.challenge + self.s)

            tmp = (
                """"lang":"zh-cn","type":"fullpage","tt":"%s","light":"DIV_0","s":"c7c3e21112fe4f741921cb3e4ff9f7cb","h":"321f9af1e098233dbd03f250fd2b5e21","hh":"39bd9cad9e425c3a8f51610fd506e3b3","hi":"09eb21b3ae9542a9bc1e8b63b3d9a467","vip_order":-1,"ct":-1,"ep":{"v":"9.1.9-dbjg5z","te":false,"me":true,"ven":"Google Inc. (Intel)","ren":"ANGLE (Intel, Intel(R) Iris(R) Xe Graphics (0x0000A7A0) Direct3D11 vs_5_0 ps_5_0, D3D11)","fp":["scroll",0,1602,1724571628498,null],"lp":["up",386,217,1724571629854,"pointerup"],"em":{"ph":0,"cp":0,"ek":"11","wd":1,"nt":0,"si":0,"sc":0},"tm":{"a":1724571567311,"b":1724571567549,"c":1724571567562,"d":0,"e":0,"f":1724571567312,"g":1724571567312,"h":1724571567312,"i":1724571567317,"j":1724571567423,"k":1724571567330,"l":1724571567423,"m":1724571567545,"n":1724571567547,"o":1724571567569,"p":1724571568259,"q":1724571568259,"r":1724571568261,"s":1724571570378,"t":1724571570378,"u":1724571570380},"dnf":"dnf","by":0},"passtime":1600,"rp":"%s","""
                % (transformed_mouse_track, rp)
            )

            r = "{" + tmp + '"captcha_token":"1198034057","du6o":"eyjf7nne"}'
            ct = self.aes_encrypt(r)
            s = [byte for byte in ct]
            w = self.encode(s)

            params = {
                "gt": self.gt,
                "challenge": self.challenge,
                "lang": "zh-cn",
                "pt": 0,
                "client_type": "web",
                "callback": "geetest_" + str(int(round(time.time() * 1000))),
                "w": w,
            }
            resp = self.session.get(
                "https://api.geetest.com/ajax.php", params=params, timeout=10
            )
            print(resp.text)
            return json.loads(resp.text[22:-1])["data"]
        except (curl_requests.exceptions.RequestException, ValueError) as e:
            log.error(f"AJAX 请求失败: {e}")
            raise

    @_retry()
    def get_pic(self, retry: int = 0) -> bytes:
        try:
            params = {
                "type": "click",
                "gt": self.gt,
                "challenge": self.challenge,
                "lang": "zh-cn",
                "callback": "geetest_" + str(int(round(time.time() * 1000))),
            }
            if retry == 0:
                url = "https://api.geevisit.com/get.php"
                params.update(
                    {
                        "is_next": "true",
                        "https": "true",
                        "protocol": "https://",
                        "offline": "false",
                        "product": "float",
                        "api_server": "api.geevisit.com",
                        "isPC": True,
                        "autoReset": True,
                        "width": "100%",
                    }
                )
            else:
                url = "https://api.geetest.com/refresh.php"

            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = json.loads(resp.text[22:-1])["data"]
            self.pic_path = data["pic"]
            pic_url = "https://" + data["image_servers"][0][:-1] + data["pic"]
            pic_resp = self.session.get(pic_url, timeout=10)
            pic_resp.raise_for_status()
            return pic_resp.content
        except (curl_requests.exceptions.RequestException, ValueError) as e:
            log.error(f"获取图片失败: {e}")
            raise

    @_retry()
    def get_c_s(self) -> tuple[list, str]:
        try:
            o = {
                "gt": self.gt,
                "challenge": self.challenge,
                "offline": False,
                "new_captcha": True,
                "product": "embed",
                "width": "300px",
                "https": True,
                "protocol": "https://",
            }
            o.update(self._get_type())
            o.update(
                {
                    "cc": 16,
                    "ww": True,
                    "i": "-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1",
                }
            )
            o = json.dumps(o, separators=(",", ":"))
            ct = self.aes_encrypt(o)
            s = [byte for byte in ct]
            i = self.encode(s)
            r = self.encrypt_key
            w = i + r
            params = {
                "gt": self.gt,
                "challenge": self.challenge,
                "lang": "zh-cn",
                "pt": 0,
                "client_type": "web",
                "callback": "geetest_" + str(int(round(time.time() * 1000))),
                "w": w,
            }
            resp = self.session.get(
                "https://api.geetest.com/get.php", params=params, timeout=10
            )
            resp.raise_for_status()
            data = json.loads(resp.text[22:-1])["data"]
            self.c = data["c"]
            self.s = data["s"]
            return self.c, self.s
        except (curl_requests.exceptions.RequestException, ValueError) as e:
            log.error(f"获取 c 和 s 失败: {e}")
            raise

    @_retry()
    def verify(self, points: list) -> str:
        try:
            u = self.encrypt_key
            current_time = int(time.time() * 1000)
            o = {
                "lang": "zh-cn",
                "passtime": 1600,
                "a": ",".join(points),
                "pic": self.pic_path,
                "tt": self.encode_mouse_path(self.mouse_track, self.c, self.s),
                "ep": {
                    "ca": [
                        {"x": 524, "y": 209, "t": 0, "dt": 1819},
                        {"x": 558, "y": 299, "t": 0, "dt": 428},
                        {"x": 563, "y": 95, "t": 0, "dt": 952},
                        {"x": 670, "y": 407, "t": 3, "dt": 892},
                    ],
                    "v": "3.1.0",
                    "$_FB": False,
                    "me": True,
                    "tm": {
                        "a": current_time - 6000,
                        "b": current_time - 5798,
                        "c": current_time - 5790,
                        "d": 0,
                        "e": 0,
                        "f": current_time - 5999,
                        "g": current_time - 5999,
                        "h": current_time - 5999,
                        "i": current_time - 5999,
                        "j": current_time - 5999,
                        "k": 0,
                        "l": current_time - 5990,
                        "m": current_time - 5802,
                        "n": current_time - 5800,
                        "o": current_time - 5785,
                        "p": current_time - 5654,
                        "q": current_time - 5654,
                        "r": current_time - 5652,
                        "s": current_time - 4335,
                        "t": current_time - 4335,
                        "u": current_time - 4334,
                    },
                },
                "h9s9": "1816378497",
            }
            o["rp"] = self.md5(self.gt + self.challenge + str(o["passtime"]))
            o = json.dumps(o, separators=(",", ":"))
            ct = self.aes_encrypt(o)
            s = [byte for byte in ct]
            p = self.encode(s)
            w = p + u
            params = {
                "gt": self.gt,
                "challenge": self.challenge,
                "lang": "zh-cn",
                "pt": 0,
                "client_type": "web",
                "w": w,
            }
            resp = self.session.get(
                "https://api.geevisit.com/ajax.php", params=params, timeout=10
            )
            resp.raise_for_status()
            return resp.text[1:-1]
        except (curl_requests.exceptions.RequestException, ValueError) as e:
            log.error(f"验证失败: {e}")
            raise


class Geetest:
    def __init__(self, gt: str = None, challenge: str = None) -> None:
        self.by = Bypass(gt, challenge)
        self.det = Detector()

    def bypass(self):
        try:
            self.by._get_type()

            self.by.get_c_s()

            self.by._ajax()

            for attempt in range(30):
                attempt_start_time = time.time()

                pic_content = self.by.get_pic(attempt)

                small_img, big_img = self.det.detect(pic_content)

                results = self.det.siamese(small_img, big_img)

                pos_lst = []
                for i in results:
                    left = str(round((i[0] + 30) / 333 * 10000))
                    top = str(round((i[1] + 30) / 333 * 10000))
                    pos_lst.append(f"{left}_{top}")

                wait_time = max(0, 2.0 - (time.time() - attempt_start_time))
                time.sleep(wait_time)

                result = json.loads(self.by.verify(pos_lst))

                if result["data"]["result"] == "success":
                    break

            return result["data"]["validate"]
        except Exception:
            raise


if __name__ == "__main__":
    resp = curl_requests.get(
        "https://passport.bilibili.com/x/passport-login/captcha",
        params={
            "source": "main-fe",
            "web_location": "333.1228",
        },
    )

    resp_json1 = resp.json()
    print(resp_json1)
    challenge = resp_json1["data"]["geetest"]["challenge"]
    gt = resp_json1["data"]["geetest"]["gt"]
    token = resp_json1["data"]["token"]
    geetest = Geetest(gt, challenge)
    print(geetest.bypass())
