# DeskOTP

Windows 10/11向けのローカルTOTP認証アプリ（試作版）。

- `otpauth://totp/...` 形式の**登録用**QRを画面または画像から読み取る
- RFC 6238に従って6/8桁の認証コードを端末内で生成
- ボタン操作後3秒待って別ウィンドウへ数字を入力（Enterは押さない）
- 複数アカウント対応。メタデータはJSON、**秘密鍵はWindows Credential Manager**へ保存

> Microsoft Authenticatorのプッシュ承認・番号照合・パスキー・サインインQRには非対応。TOTP秘密鍵を含む登録QRのみ対応。

## 起動 (Windows 10/11 + Python 3.11+)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m deskotp
```

テストと実行ファイルのビルド:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
.\build_windows.ps1
```

出力: `dist\DeskOTP\DeskOTP.exe`。Windows実機での確認は未完了。

## セキュリティ

- 登録QR/秘密鍵は**認証情報そのもの**。GitHubにコミットしたり外部送信しない。
- QRのスクリーンショットはディスクに保存しない。秘密鍵/コードはクリップボードやログに出さない。
- 同一PC上で動作するマルウェアへの完全な防御にはならない。重要なアカウントは別端末やセキュリティキーを推奨。
- 所属組織の認証ポリシーに従う。

設計: [docs/SPEC.md](docs/SPEC.md) / 開発タスク: [Issue #1](https://github.com/hglasswater-boop/DeskOTP/issues/1)
