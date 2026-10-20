============================================= test session starts =============================================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.7.0 -- D:\VS CODE\3_Python\sonicrypt\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\VS CODE\3_Python\sonicrypt\tests
plugins: anyio-4.15.1
collected 6 items                                                                                              

crypto_test.py::test_roundtrip PASSED                                                                    [ 16%]
crypto_test.py::test_nonce_random PASSED                                                                 [ 33%]
crypto_test.py::test_wrong_passphrase PASSED                                                             [ 50%]
crypto_test.py::test_various_sizes PASSED                                                                [ 66%]
crypto_test.py::test_tampered PASSED                                                                     [ 83%]
crypto_test.py::test_invalid_input PASSED                                                                [100%]

============================================== 6 passed in 0.06s ==============================================