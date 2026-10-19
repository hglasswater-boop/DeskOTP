import qrcode
import pytest
from deskotp.qr import decode_image

def test_decode_synthetic_qr(tmp_path):
    uri = "otpauth://totp/Example%3Aalice?secret=JBSWY3DPEHPK3PXP&issuer=Example"
    path = tmp_path / "otp.png"
    qrcode.make(uri).save(path)
    assert decode_image(path) == uri

def test_reject_non_totp_qr(tmp_path):
    path = tmp_path / "other.png"
    qrcode.make("https://example.com/login").save(path)
    with pytest.raises(ValueError, match="TOTP"):
        decode_image(path)
