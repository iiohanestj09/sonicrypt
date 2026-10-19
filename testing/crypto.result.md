(.venv) PS D:\VS CODE\3_Python\sonicrypt> python -i
Python 3.14.7 (tags/v3.14.7:823f032, Aug  5 2026, 10:51:32) [MSC v.1944 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
Ctrl click to launch VS Code Native REPL (https://aka.ms/python-native-repl)
>>> from src.crypto import encrypt, decrypt
... blob = encrypt(b"halo dunia", "abc")
... len(blob)
... 
38
>>> decrypt(blob, "abc")
b'halo dunia'
>>> b1 = encrypt(b"x", "abc")
... b2 = encrypt(b"x", "abc")
... b1 == b2
... 
False
>>> decrypt(blob, "salah")
Traceback (most recent call last):
  File "<python-input-3>", line 1, in <module>
    decrypt(blob, "salah")
    ~~~~~~~^^^^^^^^^^^^^^^
  File "D:\VS CODE\3_Python\sonicrypt\src\crypto.py", line 74, in decrypt
    return AESGCM(key).decrypt(nonce, ct_and_tag, None)
           ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
cryptography.exceptions.InvalidTag
>>> for size in [0, 1, 16, 1024, 1024*1024]:
...     p = b"x" * size
...     b = encrypt(p, "abc")
...     assert decrypt(b, "abc") == p
...     print(f"{size:>10} byte  ->  blob {len(b):>10} byte  OK")
...     
         0 byte  ->  blob         28 byte  OK
         1 byte  ->  blob         29 byte  OK
        16 byte  ->  blob         44 byte  OK
      1024 byte  ->  blob       1052 byte  OK
   1048576 byte  ->  blob    1048604 byte  OK
>>> b = encrypt(b"pesan penting", "abc")
... rusak = b[:-1] + bytes([b[-1] ^ 0xFF])  # ubah 1 byte terakhir
... decrypt(rusak, "abc")
... 
Traceback (most recent call last):
  File "<python-input-5>", line 3, in <module>
    decrypt(rusak, "abc")
    ~~~~~~~^^^^^^^^^^^^^^
  File "D:\VS CODE\3_Python\sonicrypt\src\crypto.py", line 74, in decrypt
    return AESGCM(key).decrypt(nonce, ct_and_tag, None)
           ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
cryptography.exceptions.InvalidTag
>>> encrypt("string bukan bytes", "abc")
Traceback (most recent call last):
  File "<python-input-6>", line 1, in <module>
    encrypt("string bukan bytes", "abc")
    ~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\VS CODE\3_Python\sonicrypt\src\crypto.py", line 48, in encrypt
    raise TypeError("plaintext harus bytes")
TypeError: plaintext harus bytes
>>> encrypt(b"x", "")
Traceback (most recent call last):
  File "<python-input-7>", line 1, in <module>
    encrypt(b"x", "")
    ~~~~~~~^^^^^^^^^^
  File "D:\VS CODE\3_Python\sonicrypt\src\crypto.py", line 49, in encrypt
    key = derive_key(passphrase)
  File "D:\VS CODE\3_Python\sonicrypt\src\crypto.py", line 35, in derive_key
    raise ValueError("passphrase tidak boleh kosong")
ValueError: passphrase tidak boleh kosong
>>> decrypt(b"pendek", "abc")
Traceback (most recent call last):
  File "<python-input-8>", line 1, in <module>
    decrypt(b"pendek", "abc")
    ~~~~~~~^^^^^^^^^^^^^^^^^^
  File "D:\VS CODE\3_Python\sonicrypt\src\crypto.py", line 67, in decrypt
    raise ValueError(
    ...<2 lines>...
    )
ValueError: blob terlalu pendek (min 28 byte, dapat 6)
>>> exit()