============================================= test session starts =============================================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.7.0 -- D:\VS CODE\3_Python\sonicrypt\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\VS CODE\3_Python\sonicrypt\tests
plugins: anyio-4.15.1
collected 7 items                                                                                              

robustness_test.py::test_baseline_success PASSED                                                         [ 14%]
robustness_test.py::test_all_attacks_fail PASSED                                                         [ 28%]
robustness_test.py::test_noise_destroys_lsb PASSED                                                       [ 42%]
robustness_test.py::test_crop_destroys_header PASSED                                                     [ 57%]
robustness_test.py::test_single_bit_tamper_ciphertext PASSED                                             [ 71%]
robustness_test.py::test_single_bit_flip_ciphertext PASSED                                               [ 85%]
robustness_test.py::test_ciphertext_noise_triggers_invalid_tag PASSED                                    [100%]

============================================== 7 passed in 1.94s ==============================================