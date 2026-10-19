=================================================== test session starts ===================================================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.7.0 -- D:\VS CODE\3_Python\sonicrypt\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\VS CODE\3_Python\sonicrypt\tests
plugins: anyio-4.15.1
collected 5 items                                                                                                          

robustness_test.py::test_baseline_success PASSED                                                                     [ 20%]
robustness_test.py::test_all_attacks_fail PASSED                                                                     [ 40%]
robustness_test.py::test_noise_destroys_lsb PASSED                                                                   [ 60%]
robustness_test.py::test_crop_destroys_header PASSED                                                                 [ 80%]
robustness_test.py::test_single_bit_tamper_ciphertext PASSED                                                         [100%]

==================================================== 5 passed in 1.58s ====================================================