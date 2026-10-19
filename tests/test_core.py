import base64
import pytest
from deskotp.core import parse_uri, totp, seconds_remaining, AccountSpec

@pytest.mark.parametrize("algorithm,secret,expected", [
    ("SHA1", "12345678901234567890", "94287082"),
    ("SHA256", "12345678901234567890123456789012", "46119246"),
    ("SHA512", "1234567890123456789012345678901234567890123456789012345678901234", "90693936"),
])
def test_rfc6238_known_vectors(algorithm, secret, expected):
    spec = AccountSpec(label="test", issuer="", account="test",
        secret=base64.b32encode(secret.encode()).decode(), algorithm=algorithm, digits=8, period=30)
    assert totp(spec, 59) == expected

def test_parse_issuer_label_and_defaults():
    spec = parse_uri("otpauth://totp/Example:alice%40example.com?secret=JBSWY3DPEHPK3PXP&issuer=Example")
    assert (spec.issuer, spec.account, spec.algorithm, spec.digits, spec.period) == ("Example", "alice@example.com", "SHA1", 6, 30)
    assert len(totp(spec, 60)) == 6

def test_parse_custom_parameters():
    spec = parse_uri("otpauth://totp/Me?secret=JBSWY3DPEHPK3PXP&algorithm=SHA256&digits=8&period=45")
    assert (spec.algorithm, spec.digits, spec.period) == ("SHA256", 8, 45)
    assert seconds_remaining(spec, 45) == 45
    assert seconds_remaining(spec, 56) == 34

@pytest.mark.parametrize("uri", [
    "https://example.com/qrcode",
    "otpauth://hotp/alice?secret=JBSWY3DPEHPK3PXP&counter=0",
    "otpauth://totp/alice?secret=",
    "otpauth://totp/alice?secret=not-valid!",
    "otpauth://totp/alice?secret=JBSWY3DPEHPK3PXP&digits=9",
    "otpauth://totp/alice?secret=JBSWY3DPEHPK3PXP&period=0",
    "otpauth://totp/alice?secret=JBSWY3DPEHPK3PXP&algorithm=MD5",
    "otpauth://totp/Other:alice?secret=JBSWY3DPEHPK3PXP&issuer=Example",
    "otpauth://totp/alice?secret=JBSWY3DPEHPK3PXP&secret=AAAAAAAA",
    "otpauth://totp/%20?secret=JBSWY3DPEHPK3PXP",
])
def test_reject_bad_uris(uri):
    with pytest.raises(ValueError):
        parse_uri(uri)
