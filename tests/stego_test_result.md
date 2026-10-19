=================================================== test session starts ===================================================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.7.0 -- D:\VS CODE\3_Python\sonicrypt\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\VS CODE\3_Python\sonicrypt\tests
plugins: anyio-4.15.1
collected 6 items                                                                                                          

stego_test.py::test_read_valid_wav PASSED                                                                            [ 16%]
stego_test.py::test_write_read_roundtrip PASSED                                                                      [ 33%]
stego_test.py::test_read_missing_file PASSED                                                                         [ 50%]
stego_test.py::test_read_non_16bit_rejected PASSED                                                                   [ 66%]
stego_test.py::test_write_invalid_samples PASSED                                                                     [ 83%]
stego_test.py::test_write_size_mismatch PASSED                                                                       [100%]

==================================================== 6 passed in 1.17s ====================================================