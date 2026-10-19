python -i

# Test 2.1 — Round-trip sederhana 
from src.crypto import encrypt, decrypt
blob = encrypt(b"halo dunia", "abc")
len(blob)
> Ekspektasi: 38

decrypt(blob, "abc")
> Ekspektasi: b'halo dunia'

# Test 2.2 — Nonce acak, output berbeda
b1 = encrypt(b"x", "abc")
b2 = encrypt(b"x", "abc")
b1 == b2
> Ekspektasi: False

# Test 2.3 — Passphrase salah → error
decrypt(blob, "salah")
> Ekspektasi: exception InvalidTag dari cryptography.exceptions

# Test 2.4 — Berbagai ukuran plaintext
for size in [0, 1, 16, 1024, 1024*1024]:
    p = b"x" * size
    b = encrypt(p, "abc")
    assert decrypt(b, "abc") == p
    print(f"{size:>10} byte  ->  blob {len(b):>10} byte  OK")
> Ekspektasi:
          0 byte  ->  blob         28 byte  OK
          1 byte  ->  blob         29 byte  OK
         16 byte  ->  blob         44 byte  OK
       1024 byte  ->  blob       1052 byte  OK
    1048576 byte  ->  blob    1048604 byte  OK

# Test 2.5 — Data di-tamper
b = encrypt(b"pesan penting", "abc")
rusak = b[:-1] + bytes([b[-1] ^ 0xFF])
decrypt(rusak, "abc")
> Ekspektasi: raise InvalidTag  

# Test 2.6 — Input invalid
encrypt("string bukan bytes", "abc")
> Ekspektasi: TypeError: plaintext harus bytes

encrypt(b"x", "")
> Ekspektasi: ValueError: passphrase tidak boleh kosong

decrypt(b"pendek", "abc")
> Ekspektasi: ValueError: blob terlalu pendek ...