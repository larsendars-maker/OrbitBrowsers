import base64
import ctypes
import ctypes.wintypes
import json
import os

if os.name == "nt":
    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", ctypes.wintypes.DWORD),
                    ("pbData", ctypes.POINTER(ctypes.c_byte))]

    def _blob(data: bytes):
        buf = (ctypes.c_byte * len(data)).from_buffer_copy(data)
        return DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte)))

    def protect(data: str) -> str:
        raw = data.encode("utf-8")
        inp = _blob(raw)
        out = DATA_BLOB()
        if not ctypes.windll.crypt32.CryptProtectData(ctypes.byref(inp), None, None, None, None, 0, ctypes.byref(out)):
            raise OSError("CryptProtectData failed")
        try:
            value = ctypes.string_at(out.pbData, out.cbData)
            return "dpapi:" + base64.b64encode(value).decode("ascii")
        finally:
            ctypes.windll.kernel32.LocalFree(out.pbData)

    def unprotect(value: str) -> str:
        if not value.startswith("dpapi:"):
            raise ValueError("Unsupported secure value")
        raw = base64.b64decode(value[6:])
        inp = _blob(raw)
        out = DATA_BLOB()
        if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(inp), None, None, None, None, 0, ctypes.byref(out)):
            raise OSError("CryptUnprotectData failed")
        try:
            return ctypes.string_at(out.pbData, out.cbData).decode("utf-8")
        finally:
            ctypes.windll.kernel32.LocalFree(out.pbData)
else:
    def protect(data: str) -> str:
        raise RuntimeError("DPAPI is available only on Windows")

    def unprotect(value: str) -> str:
        raise RuntimeError("DPAPI is available only on Windows")
