"""Simple local Tkinter GUI."""
from __future__ import annotations
from pathlib import Path
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from .core import AccountSpec, parse_uri, seconds_remaining, totp
from .storage import Account, AccountStore, default_data_path
from .typing import type_into_foreground

class DeskOTPApp:
    def __init__(self, root: tk.Tk):
        if sys.platform != "win32":
            raise RuntimeError("DeskOTPアプリはWindows専用です。")
        from keyring.backends.Windows import WinVaultKeyring
        self.root = root
        self.store = AccountStore(default_data_path(), WinVaultKeyring())
        self.accounts: list[Account] = []
        self.selected_spec: AccountSpec | None = None
        self.selected_id: str | None = None
        self.pending_input = False
        root.title("DeskOTP - ワンタイム認証コード")
        root.geometry("585x420")
        root.minsize(480, 340)
        frame = ttk.Frame(root, padding=14)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="DeskOTP", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(frame, text="標準TOTP登録QR専用 / 端末内でコードを生成", foreground="#555").pack(anchor="w", pady=(0, 12))
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill="x", pady=(0, 10))
        ttk.Button(toolbar, text="画面QR登録", command=self.scan_screen).pack(side="left", padx=(0, 8))
        ttk.Button(toolbar, text="画像QR登録", command=self.scan_file).pack(side="left", padx=(0, 8))
        ttk.Button(toolbar, text="選択を削除", command=self.remove_account).pack(side="right")
        ttk.Label(frame, text="アカウント").pack(anchor="w")
        listframe = ttk.Frame(frame)
        listframe.pack(fill="both", expand=True, pady=(4, 10))
        self.listbox = tk.Listbox(listframe, height=6, font=("Segoe UI", 11), exportselection=False)
        self.listbox.pack(fill="both", expand=True, side="left")
        scroll = ttk.Scrollbar(listframe, orient="vertical", command=self.listbox.yview)
        scroll.pack(side="right", fill="y")
        self.listbox.configure(yscrollcommand=scroll.set)
        self.listbox.bind("<<ListboxSelect>>", self.on_selected)
        info = ttk.Frame(frame)
        info.pack(fill="x", pady=(0, 7))
        self.code_text = tk.StringVar(value="------")
        self.timer_text = tk.StringVar(value="QRを登録してください")
        ttk.Label(info, textvariable=self.code_text, font=("Consolas", 26, "bold")).pack(side="left")
        ttk.Label(info, textvariable=self.timer_text).pack(side="right")
        bottom = ttk.Frame(frame)
        bottom.pack(fill="x")
        self.type_button = ttk.Button(bottom, text="3秒後に入力", command=self.schedule_type)
        self.type_button.pack(side="left")
        self.status = tk.StringVar(value="入力時は3秒以内に対象の入力欄をクリックしてください。")
        ttk.Label(frame, textvariable=self.status, wraplength=550, foreground="#555").pack(anchor="w", pady=(10, 0))
        self.refresh_accounts()
        self.update_code()

    def refresh_accounts(self, select_id: str | None = None) -> None:
        self.accounts = self.store.list_accounts()
        self.listbox.delete(0, tk.END)
        for account in self.accounts:
            label = f"{account.issuer} — {account.account}" if account.issuer else account.account
            self.listbox.insert(tk.END, label)
        index = next((i for i, a in enumerate(self.accounts) if a.id == select_id), 0)
        if self.accounts:
            self.listbox.selection_set(index)
            self.listbox.see(index)
        self.on_selected()

    def on_selected(self, _event=None) -> None:
        picked = self.listbox.curselection()
        if not picked:
            self.selected_id = None
            self.selected_spec = None
            return
        candidate = self.accounts[picked[0]].id
        if candidate == self.selected_id and self.selected_spec:
            return
        try:
            self.selected_spec = self.store.get_spec(candidate)
            self.selected_id = candidate
        except (LookupError, ValueError) as exc:
            self.selected_spec = None
            self.selected_id = None
            messagebox.showerror("資格情報エラー", str(exc), parent=self.root)

    def update_code(self) -> None:
        if self.selected_spec is None:
            self.code_text.set("------")
            self.timer_text.set("未選択")
        else:
            self.code_text.set(totp(self.selected_spec))
            self.timer_text.set(f"あと {seconds_remaining(self.selected_spec)} 秒")
        self.root.after(250, self.update_code)

    def _add_qr(self, uri: str) -> None:
        account = self.store.add(parse_uri(uri))
        self.refresh_accounts(select_id=account.id)
        self.status.set("登録しました。コードが正しいことをサービス側で確認してください。")

    def scan_screen(self) -> None:
        self.root.withdraw()
        self.root.after(400, self._capture_screen)

    def _capture_screen(self) -> None:
        try:
            from .qr import decode_screen
            self._add_qr(decode_screen())
        except Exception as exc:
            self.root.deiconify()
            messagebox.showerror("QR読み取り", str(exc), parent=self.root)
        finally:
            self.root.deiconify()

    def scan_file(self) -> None:
        filename = filedialog.askopenfilename(parent=self.root, title="TOTP登録QRの画像を選択",
                                              filetypes=[("画像ファイル", "*.png *.jpg *.jpeg *.bmp *.webp"), ("すべて", "*.*")])
        if not filename:
            return
        try:
            from .qr import decode_image
            self._add_qr(decode_image(Path(filename)))
        except Exception as exc:
            messagebox.showerror("QR読み取り", str(exc), parent=self.root)

    def remove_account(self) -> None:
        if not self.selected_id:
            return
        selected = next((a for a in self.accounts if a.id == self.selected_id), None)
        if selected is None:
            return
        if not messagebox.askyesno("削除の確認", f"{selected.account} の登録と秘密鍵を削除しますか？", parent=self.root):
            return
        try:
            self.store.remove(selected.id)
            self.selected_spec = None
            self.selected_id = None
            self.refresh_accounts()
            self.status.set("登録を削除しました。")
        except Exception as exc:
            messagebox.showerror("削除エラー", str(exc), parent=self.root)

    def schedule_type(self) -> None:
        if self.pending_input or self.selected_id is None:
            return
        self.pending_input = True
        account_id = self.selected_id
        self.type_button.state(["disabled"])
        self.status.set("3秒以内に入力先アプリのコード入力欄にフォーカスを移してください…")
        self.root.after(3000, lambda: self._type_selected(account_id))

    def _type_selected(self, account_id: str) -> None:
        try:
            spec = self.store.get_spec(account_id)
            if seconds_remaining(spec) <= 5:
                raise RuntimeError("コードの期限が近いため中止しました。更新後に再試行してください。")
            type_into_foreground(totp(spec))
            self.status.set("コードを入力しました（Enterは押していません）。")
        except Exception as exc:
            self.status.set(f"自動入力を中止: {exc}")
        finally:
            self.pending_input = False
            self.type_button.state(["!disabled"])

def main() -> None:
    root = tk.Tk()
    try:
        DeskOTPApp(root)
    except Exception as exc:
        messagebox.showerror("起動エラー", str(exc), parent=root)
        root.destroy()
        return
    root.mainloop()
