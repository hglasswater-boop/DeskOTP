"""QR decoding in memory (no screenshot files)."""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageGrab
import cv2
import numpy as np
from .core import parse_uri

def decode_pil(image: Image.Image) -> str:
    bgr = cv2.cvtColor(np.asarray(image.convert("RGB")), cv2.COLOR_RGB2BGR)
    scanner = cv2.QRCodeDetector()
    decoded: list[str] = []
    try:
        found, strings, _, _ = scanner.detectAndDecodeMulti(bgr)
        if found:
            decoded.extend(s for s in strings if s)
    except cv2.error:
        pass
    if not decoded:
        value, _, _ = scanner.detectAndDecode(bgr)
        if value:
            decoded.append(value)
    if not decoded:
        raise ValueError("画像からQRコードを読み取れませんでした。")
    valid = []
    for value in decoded:
        try:
            parse_uri(value)
        except ValueError:
            continue
        valid.append(value)
    if not valid:
        raise ValueError("対応するTOTP登録QRがありません（ログインQR・HOTP等には非対応）。")
    if len(valid) > 1:
        raise ValueError("TOTP登録QRが複数あります。1つだけ表示して再試行してください。")
    return valid[0]

def decode_image(path: str | Path) -> str:
    with Image.open(path) as image:
        return decode_pil(image)

def decode_screen() -> str:
    screenshot = ImageGrab.grab(all_screens=True)
    try:
        return decode_pil(screenshot)
    finally:
        screenshot.close()
