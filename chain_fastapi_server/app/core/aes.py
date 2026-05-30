"""AES-CBC 加密解密模块。

使用 AES-128-CBC 模式 + PKCS7 填充，密文以十六进制字符串传输。
依赖: pycryptodome
"""

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from binascii import b2a_hex, a2b_hex


class Aescrypt:
    """AES-CBC 加密解密工具类。

    Args:
        key: 16 / 24 / 32 字节的密钥字符串。
    """

    def __init__(self, key: str):
        self.key = key.encode("utf-8")
        self.mode = AES.MODE_CBC
        self._iv = b"0000000000000000"  # 与 chain_wms_api 保持一致

    def encrypt(self, text: str) -> str:
        """加密明文，返回十六进制密文字符串。"""
        text_bytes = text.encode("utf-8")
        cipher = AES.new(self.key, self.mode, self._iv)
        encrypted = cipher.encrypt(pad(text_bytes, AES.block_size))
        return b2a_hex(encrypted).decode()

    def decrypt(self, hex_text: str) -> str:
        """解密十六进制密文，返回明文字符串。"""
        cipher = AES.new(self.key, self.mode, self._iv)
        decrypted = cipher.decrypt(a2b_hex(hex_text))
        return unpad(decrypted, AES.block_size).decode("utf-8")
