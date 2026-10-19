import json
import pytest
from deskotp.core import parse_uri
from deskotp.storage import AccountStore

class FakeKeyring:
    def __init__(self):
        self.items = {}
    def set_password(self, service, key, value):
        self.items[(service, key)] = value
    def get_password(self, service, key):
        return self.items.get((service, key))
    def delete_password(self, service, key):
        del self.items[(service, key)]

def test_add_retrieve_delete_without_secret_in_json(tmp_path):
    backend = FakeKeyring()
    store = AccountStore(tmp_path / "accounts.json", backend)
    spec = parse_uri("otpauth://totp/Site:bob?secret=JBSWY3DPEHPK3PXP&issuer=Site")
    account = store.add(spec)
    text = (tmp_path / "accounts.json").read_text()
    assert "JBSWY3DPEHPK3PXP" not in text
    assert len(json.loads(text)) == 1
    assert store.get_spec(account.id) == spec
    with pytest.raises(ValueError, match="登録済み"):
        store.add(spec)
    store.remove(account.id)
    assert store.list_accounts() == []
    assert not backend.items

def test_missing_credential_reported(tmp_path):
    backend = FakeKeyring()
    store = AccountStore(tmp_path / "accounts.json", backend)
    account = store.add(parse_uri("otpauth://totp/A?secret=JBSWY3DPEHPK3PXP"))
    backend.delete_password("DeskOTP", account.id)
    with pytest.raises(LookupError):
        store.get_spec(account.id)
