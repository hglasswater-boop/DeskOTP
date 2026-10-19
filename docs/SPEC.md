# DeskOTP - 仕様・セキュリティ設計

## フロー
1. ユーザーがサービスのTOTP登録用QRを自分の画面に表示、または自分の画像ファイルから選択する。
2. OpenCVが画像をメモリ内で解析。otpauth://totp/ のみ受理。QRスクリーンショットは保存しない。
3. アカウント情報は %LOCALAPPDATA%\DeskOTP\accounts.json（秘密鍵なし）。秘密鍵はWindowsユーザーのCredential Manager（keyring）に保存する。
4. 標準ライブラリのHMACでRFC 6238 TOTPをオフライン計算。
5. ユーザーが「3秒後に入力」を押し、その間に別アプリの入力欄を選択する。フォアグラウンドが本アプリの場合は入力を拒否。数字のみ、Enterは送信しない。

## 対応・非対応
- 対応：登録用otpauth://totp URI、Base32秘密鍵、SHA1/256/512、6/8桁、1〜300秒周期、画面/画像QR、複数アカウント。
- 非対応：otpauth://hotp、Microsoft Authenticatorのプッシュ承認・番号照合、FIDO2/パスキー、ログインQR、スマホからの既存秘密鍵抽出、クラウド同期。

## 脅威モデル
- 秘密鍵・TOTPコード・QR画像はログやクリップボードへ書き込まない。
- Credential Managerを利用しても同じWindowsユーザー権限のマルウェアには完全には対抗できない。
- 特権ウィンドウやセキュアデスクトップへのSendInputはサポートしない。
- 画面QR読み取りはユーザーの明示操作時のみ。画像をクラウドへ送信しない。
- 登録QRは認証秘密鍵を含むためGitHub、メール、チャットへ共有しない。

## モジュール
- deskotp/core.py: URI解析とTOTP生成
- deskotp/qr.py: QR解析
- deskotp/storage.py: アカウント情報とCredential Manager
- deskotp/typing.py: Win32 SendInput
- deskotp/gui.py: Tkinter画面

## Windowsでの受け入れ試験（未実施）
1. 合成のテストQRを画面/PNGから追加し独立した認証器とコードが一致すること。
2. 重複登録が拒否されること。
3. メモ帳へ手動トリガーで正確に6/8桁を入力し、改行を付けないこと。
4. DeskOTP自身が最前面のままなら入力しないこと。
5. 再起動後に登録が残り、JSONに秘密鍵がないこと。
6. アカウント削除が反映されること。
7. 高DPI/マルチディスプレイ上のQR読み取りを確認すること。
8. WindowsでPyInstallerビルドしてEXE起動を確認すること。
