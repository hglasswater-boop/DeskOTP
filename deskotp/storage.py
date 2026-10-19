"""Nonsecret account metadata and Windows Credential Manager backend."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import tempfile
import uuid
from .core import AccountSpec

SERVICE = "DeskOTP"

@dataclass(frozen=True)
class Account:
    id: str
    label: str
    issuer: str
    account: str
    algorithm: str
    digits: int
    period: int

def default_data_path() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        base = str(Path.home() / "AppData" / "Local")
    return Path(base) / SERVICE / "accounts.json"

class AccountStore:
    def __init__(self, path: Path, credential_backend: object):
        self.path = Path(path)
        self.credentials = credential_backend

    def list_accounts(self) -> list[Account]:
        if not self.path.exists():
            return []
        rows = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(rows, list):
            raise ValueError("アカウント情報ファイルが破損しています。")
        return [Account(**row) for row in rows]

    def _save(self, accounts: list[Account]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, filename = tempfile.mkstemp(prefix="accounts-", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as file:
                json.dump([asdict(a) for a in accounts], file, ensure_ascii=False, indent=2)
            os.replace(filename, self.path)
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def add(self, spec: AccountSpec) -> Account:
        old = self.list_accounts()
        if any((a.issuer.casefold(), a.account.casefold()) ==
               (spec.issuer.casefold(), spec.account.casefold()) for a in old):
            raise ValueError("同じサービス・アカウントが登録済みです。")
        account = Account(uuid.uuid4().hex, spec.label, spec.issuer, spec.account,
                          spec.algorithm, spec.digits, spec.period)
        self.credentials.set_password(SERVICE, account.id, spec.secret)
        try:
            self._save([*old, account])
        except Exception:
            self.credentials.delete_password(SERVICE, account.id)
            raise
        return account

    def get_spec(self, account_id: str) -> AccountSpec:
        account = next((a for a in self.list_accounts() if a.id == account_id), None)
        if account is None:
            raise LookupError("アカウントが見つかりません。")
        secret = self.credentials.get_password(SERVICE, account.id)
        if not secret:
            raise LookupError("資格情報マネージャーから秘密鍵を取得できません。")
        return AccountSpec(account.label, account.issuer, account.account,
                           secret, account.algorithm, account.digits, account.period)

    def remove(self, account_id: str) -> None:
        accounts = self.list_accounts()
        if not any(a.id == account_id for a in accounts):
            raise LookupError("アカウントが見つかりません。")
        self.credentials.delete_password(SERVICE, account_id)
        self._save([a for a in accounts if a.id != account_id])
