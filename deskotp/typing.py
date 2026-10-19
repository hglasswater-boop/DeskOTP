"""Explicit Windows keyboard simulation: digits only, no Enter."""
import ctypes
from ctypes import wintypes
import os
import sys

def type_into_foreground(code: str) -> None:
    if not code.isascii() or not code.isdigit() or len(code) not in (6, 8):
        raise ValueError("6桁または8桁の数字のみ入力できます。")
    if not sys.platform.startswith("win"):
        raise RuntimeError("自動入力はWindowsでのみ使用できます。")
    user32 = ctypes.windll.user32
    user32.GetForegroundWindow.restype = wintypes.HWND
    handle = user32.GetForegroundWindow()
    if not handle:
        raise RuntimeError("入力先のウィンドウが見つかりません。")
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId(handle, ctypes.byref(pid))
    if pid.value == os.getpid():
        raise RuntimeError("入力欄のある別アプリへフォーカスを移してください。")
    uintptr = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong
    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                    ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD), ("dwExtraInfo", uintptr)]
    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                    ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                    ("dwExtraInfo", uintptr)]
    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD),
                    ("wParamH", wintypes.WORD)]
    class DATA(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]
    class INPUT(ctypes.Structure):
        _fields_ = [("type", wintypes.DWORD), ("data", DATA)]
    events = []
    for char in code:
        virtual_key = ord(char)
        events.extend([INPUT(1, DATA(ki=KEYBDINPUT(virtual_key, 0, 0, 0, 0))),
                       INPUT(1, DATA(ki=KEYBDINPUT(virtual_key, 0, 0x0002, 0, 0)))])
    payload = (INPUT * len(events))(*events)
    user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
    user32.SendInput.restype = wintypes.UINT
    sent = user32.SendInput(len(events), payload, ctypes.sizeof(INPUT))
    if sent != len(events):
        raise OSError("自動入力が完了しませんでした。管理者権限の入力欄等には入力できません。")
