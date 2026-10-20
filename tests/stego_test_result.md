============================================= test session starts =============================================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.7.0 -- D:\VS CODE\3_Python\sonicrypt\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\VS CODE\3_Python\sonicrypt\tests
plugins: anyio-4.15.1
collected 20 items                                                                                             

stego_test.py::test_read_valid_wav PASSED                                                                [  5%]
stego_test.py::test_write_read_roundtrip PASSED                                                          [ 10%]
stego_test.py::test_read_missing_file PASSED                                                             [ 15%]
stego_test.py::test_read_non_16bit_rejected PASSED                                                       [ 20%]
stego_test.py::test_write_invalid_samples PASSED                                                         [ 25%]
stego_test.py::test_write_size_mismatch PASSED                                                           [ 30%]
stego_test.py::test_bytes_to_bits_msb_first PASSED                                                       [ 35%]
stego_test.py::test_bytes_bits_roundtrip PASSED                                                          [ 40%]
stego_test.py::test_bits_to_bytes_bad_length PASSED                                                      [ 45%]
stego_test.py::test_bits_to_bytes_bad_values PASSED                                                      [ 50%]
stego_test.py::test_bytes_to_bits_bad_input PASSED                                                       [ 55%]
stego_test.py::test_embed_extract_roundtrip PASSED                                                       [ 60%]
stego_test.py::test_embed_capacity_exceeded PASSED                                                       [ 65%]
stego_test.py::test_extract_capacity_exceeded PASSED                                                     [ 70%]
stego_test.py::test_embed_does_not_modify_input PASSED                                                   [ 75%]
stego_test.py::test_embed_extract_various_sizes PASSED                                                   [ 80%]
stego_test.py::test_embed_snr_high PASSED                                                                [ 85%]
stego_test.py::test_embed_lsb_correct PASSED                                                             [ 90%]
stego_test.py::test_extract_negative_nbytes PASSED                                                       [ 95%]
stego_test.py::test_extract_zero_bytes PASSED                                                            [100%]

============================================= 20 passed in 0.35s ==============================================