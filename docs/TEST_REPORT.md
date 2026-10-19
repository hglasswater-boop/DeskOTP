# テストレポート（2026-10-19）

- Linux / Python 3.13.5: `python -m pytest -q` — **26 passed** （ローカル試作版にて）
- `python -m compileall -q deskotp launch.py` — 成功
- RFC 6238 SHA1/SHA256/SHA512既知ベクトル、合成QR、鍵の非平文保存（偽バックエンド）、入力検証を確認。
- Windows GUI / 実Credential Manager / SendInput / EXE動作: **未確認**。
- 実アカウントの秘密鍵は一切使用していない。

GitHub Actions結果は実行後に確認すること。Windows上で実行されるまでリリース済みとはみなさない。
