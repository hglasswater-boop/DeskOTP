"""RFC 6238 logic and TOTP enrollment URI parser."""
from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import hmac
import struct
import time
from urllib.parse import parse_qs, unquote, urlsplit

_HASHES = {"SHA1": hashlib.sha1, "SHA256": hashlib.sha256, "SHA512": hashlib.sha512}

@dataclass(frozen=True)
class AccountSpec:
    label: str
    issuer: str
    account: str
    secret: str
    algorithm: str = "SHA1"
    digits: int = 6
    period: int = 30

def _decode_secret(secret: str) -> bytes:
    clean = secret.strip().replace(" ", "").upper()
    if not clean:
        raise ValueError("秘密鍵がありません。")
    try:
        data = base64.b32decode(clean + "=" * (-len(clean) % 8), casefold=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError("秘密鍵のBase32形式が不正です。") from exc
    if not data:
        raise ValueError("秘密鍵が空です。")
    return data

def parse_uri(uri: str) -> AccountSpec:
    """Only accepts an otpauth://totp/ enrollment URI, never a login QR."""
    parsed = urlsplit(uri.strip())
    if parsed.scheme.lower() != "otpauth" or parsed.netloc.lower() != "totp" or parsed.fragment:
        raise ValueError("標準TOTPの登録QR（otpauth://totp/）ではありません。")
    label = unquote(parsed.path.lstrip("/")).strip()
    if not label:
        raise ValueError("アカウント名がありません。")
    params = parse_qs(parsed.query, keep_blank_values=True)
    for name in ("secret", "issuer", "algorithm", "digits", "period"):
        if len(params.get(name, [])) > 1:
            raise ValueError("QRの登録情報に重複した項目があります。")
    secret = params.get("secret", [""])[0].strip().replace(" ", "").upper()
    _decode_secret(secret)
    label_issuer, sep, label_account = label.partition(":")
    issuer = params.get("issuer", [""])[0].strip()
    if sep and issuer and label_issuer != issuer:
        raise ValueError("QRの発行元情報が一致しません。")
    if sep and not label_account.strip():
        raise ValueError("アカウント名がありません。")
    account = label_account.strip() if sep else label
    issuer = issuer or (label_issuer.strip() if sep else "")
    algorithm = params.get("algorithm", ["SHA1"])[0].upper()
    if algorithm not in _HASHES:
        raise ValueError("未対応のハッシュ方式です。")
    try:
        digits = int(params.get("digits", ["6"])[0])
        period = int(params.get("period", ["30"])[0])
    except ValueError as exc:
        raise ValueError("コード桁数・更新間隔が不正です。") from exc
    if digits not in (6, 8) or not 1 <= period <= 300:
        raise ValueError("コード桁数または更新間隔が未対応です。")
    return AccountSpec(label, issuer, account, secret, algorithm, digits, period)

def totp(spec: AccountSpec, at: int | float | None = None) -> str:
    now = time.time() if at is None else at
    counter = int(now) // spec.period
    digest = hmac.new(_decode_secret(spec.secret), struct.pack(">Q", counter), _HASHES[spec.algorithm]).digest()
    offset = digest[-1] & 0x0F
    truncated = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(truncated % (10 ** spec.digits)).zfill(spec.digits)

def seconds_remaining(spec: AccountSpec, at: int | float | None = None) -> int:
    now = time.time() if at is None else at
    return spec.period - (int(now) % spec.period)
